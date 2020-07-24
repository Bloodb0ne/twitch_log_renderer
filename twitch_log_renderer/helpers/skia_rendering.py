import skia
import numpy as np
import contextlib
import uharfbuzz as hb

def empty_np_buffer(w,h):
    return np.zeros((h, w, 4), dtype=np.uint8)

@contextlib.contextmanager
def skia_canvas(w,h):
    surface = skia.Surface(w,h)
    canvas = surface.getCanvas()
    yield canvas

def hb_string_to_tag(s):
    return (ord(s[0]) & 0xFFFFFFFF) << 24 | (ord(s[1]) & 0xFFFFFFFF) << 16 | (ord(s[2]) & 0xFFFFFFFF) << 8 | ord(s[3]) & 0xFFFFFFFF

class TypefaceTableCache:
	typefaces = {}
	
	def getTypefaceData(skia_typeface):
		familyName = skia_typeface.getFamilyName()
		data = TypefaceTableCache.typefaces.get(familyName,False)
		if not data:
			data = TypefaceTableCache.setTypefaceData(skia_typeface)
		return data
	
	def setTypefaceData(skia_typeface):
		if not skia_typeface:
			return False
		familyName = skia_typeface.getFamilyName()
		TypefaceTableCache.typefaces[familyName] = { tag: skia_typeface.getTableData(tag) for tag in skia_typeface.getTableTags()}
		return TypefaceTableCache.typefaces[familyName]

def getTextRuns(string,font,fmgr):
	lists = []
	cRun = {'font':font,'str':[]}
	lst_font = font
	for uchar in string:
		codepoint = ord(uchar)
		glyph = lst_font.unicharToGlyph(codepoint)
		default_glyph = font.unicharToGlyph(codepoint)
		
		if not glyph:
			# We cant match with the current font
			lists.append(cRun)
			# Find new font
			alt_font = fmgr.matchFamilyStyleCharacter(font.getTypeface().getFamilyName(),font.getTypeface().fontStyle(),[''],codepoint)
			if alt_font:
				glyph = alt_font.unicharToGlyph(codepoint)
				lst_font = skia.Font(alt_font,font.getSize())
				cRun = {'font':lst_font,'str':[uchar]}
		else:
			if default_glyph == glyph and lst_font != font:
				lists.append(cRun)
				cRun = {'font':font,'str':[uchar]}
				lst_font = font
			else:
				cRun['str'].append(uchar)
		
	lists.append(cRun)
	return lists

def getSkiaFontTable(face,tag,data):
	int_tag = hb_string_to_tag(tag)
	return data.get(int_tag,None)

def shaper(s,tf,size):
		face = hb.Face.create_for_tables(getSkiaFontTable,tf)
		font = hb.Font(face)
		upem = size * 64.0
		font.scale = (upem, upem)
		hb.ot_font_set_funcs(font)
		buf = hb.Buffer()

		buf.add_utf8(s.encode('utf-8'))
		# buf.add_str(s)
		buf.guess_segment_properties()

		features = {"kern": True, "liga": True}
		# features = {}
		hb.shape(font, buf, features)

		infos = buf.glyph_infos
		positions = buf.glyph_positions
		glyphs = [info.codepoint for info in infos]
		positions = [(pos.x_advance/64.0,pos.x_offset/64.0,pos.y_offset/64.0) for pos in positions]
		return (glyphs,positions)
		

def shapeStringToSkBlob(s,text_font,font_manager):
	txt_runs = getTextRuns(s,text_font,font_manager)
	tbb_ = skia.TextBlobBuilder()
	adv = 0.0
	for run in txt_runs:
		font = run['font']
		tf = font.getTypeface()
		fontSize = font.getSize()
		text = ''.join(run['str'])
		glyphs,positions = shaper(text,TypefaceTableCache.getTypefaceData(tf),fontSize)
		spositions = []
		su = adv
		for p in positions:
			spositions.append(su)
			su+=p[0]
		tbb_.allocRunPosH(font,glyphs,spositions,0.0)
		adv += su  # sum([x[0]+x[1] for x in positions],0.0)
	return (tbb_.make(),adv)

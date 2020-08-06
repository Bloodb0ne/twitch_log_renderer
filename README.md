# Twitch Log Renderer

Rendering of different styles of twitch logs ( downloaded or captured by a 3rd party software)
The interface allows for different render outputs including video, html and image.
Because the whole tool depends on 3rd party information ( emote data and user ids ) there is a need for a storage mechanism, in this case a sqlite database.

## Usage
The release zip file contains a python wheel package, you would need python 3.7+ and pip to install it 

```
 pip install <path_to_whl_file> 
```

This will add the tool to your python bin directory and you will be able to use it running 
```twitch_log_renderer``` from anywhere.

## Examples

### Downloading all twitch emotes ( this is needed for non-twitch logs)

```bash
twitch_log_renderer download emotes twitch --global --database my_database.db 
```

### Download third party emotes 

```bash
twitch_log_renderer download emotes bttv ffz --channel one two three  --database my_database.db 
```

this will download all ffz and bttv emotes for the channels with usernames *one*,*two* and *three*


### Downloading a log and rendering it with default options

```bash
twitch_log_renderer download log 1234567 --output log_name.json
twitch_log_renderer video --database my_database.db --input log_name.json --output video_file.mp4 --channel someone
```
specifying channel is needed for proper emote loading

### Inspecting a log file
```bash
twitch_log_renderer inspect log_name.json
```

### Rendering with one of the predefined config files

```bash
twitch_log_renderer video --input log_name.json --channel test --config light_theme.json
```



## Required Options

**--database**

Path to the database file,if the file does not exist it will be created
and initialized.

**--channel**

A single channel or a list of channels, can be actual channel ids or even channel names, mix and matching is allowed

**--input**

Path to the log we want to render
(link to section describing what log files are allowed)

**--output**

Output destination of the render result

**--start**

At what time should the render be started 
[Time Formats](#time-formats)

**--end**

At what time should the render end
[Time Formats](#time-formats)

**--include_timestamps**

If the log should include timestamps

**--timestamp_format**

Timestamp format based on strptime()
[Format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
    
****--include_badges****

Should the user chat badges be included

**--emote_override**

**Not Implemented**

JSON file that maps emote names to emote url/paths so they can be override/replace current or unknown ones

**--config**
    
Path to a JSON file containing predefined options, options passed normally to the command line overrride it.
The folder "example", you can find example configurations
    
    

# HTML Options

**--template_path**

Path to a html file thats used to create the resulting chat render
If not specified there is a default template that gets used. Custom templates should just include the text *$content* where they want the 
rendered messages to be put.


# Video Options

**--transparent**

Should transparency be encoded into the video, if the encoder does not support an alpha channel an additional output file will be generated containing the Alpha channel information. This file could be used as an alternative to chroma key masking based on color

**--encoder**

## Available encoders options:
    
# Without Alpha channel

- "nvenc"
    
    **file extension: .mp4**

- "h264"
    
    **file extension: .mp4**

- "h265"
    
    **file extension: .mp4**

- "vp8"
    
    **file extension: .webm**

- "vp9"
    
    **file extension: .webm**

# With Alpha channel

- "prores"

    Adobe Prores ( alpha channel reduced to 8bit)
    **file extension: .mov**

- "qtanim"
    
    Quicktime Animation
    **file extension: .mov**

- "png"
    
    Another Quicktime format
    **file extension: .mov**

- "vp8"
        
    **file extension: .webm**

- "vp9"

    **file extension: .webm**

    Some encoders might support other container formats for example not everything should be mp4, it could be wrapped in another container( the tool depends on ffmpeg so its based on what ffmpeg supports )

**--width**

[integer]
Determines the horizontal dimention of the video

**--height**

[integer]
Determines the vertical dimention of the video

**--fps**

[float]
What framerate the encoder should use

**--line_height**

Height of individual chat lines ( not the message ), all text and images are centered on the chat line. Depending on the font size this introduces top and bottom padding to each chat line.

**--image_scale**

[float][0..1]
What scaling should be applied to all image elements ( badges and emotes ). The value 1 denotes full size of the images and is the default.

**--txt_font**

[string]
Name of the font to use for username rendering, should be the name of a font installed on the system

**--txt_color**
    
[string]
Color of the text formatted in hex rgb ( **#FFFFFF** ) or hex argb ( **#FFFFFFFF** ) [Color Values](#color-values)

**--txt_font_size**
    
[float]
Size of the textual elements in chat

**--uname_font**
    
[string]
Name of the font to use for username rendering, should be the name of a font installed on the system

**--uname_font_size**

[integer]
Size of the usernames ( usernames are rendered with a **bold** fontface if that is available )

**--bg**

[string][color]
Color of the chat background in hex rgb ( **#FFFFFF** ) or hex argb ( **#FFFFFFFF** )
[Color Values](#color-values)

**--even_bg**

[string][color]
Background color of even chat messages in hex rgb ( **#FFFFFF** ) or hex argb ( **#FFFFFFFF** )
[Color Values](#color-values)

**--odd_bg**
    
[string][color]
Background color of odd chat messages in hex rgb ( **#FFFFFF** ) or hex argb ( **#FFFFFFFF** )
[Color Values](#color-values)

**--fadeout**
    
[float]
This value describes how fast the messages will need to slide out of the screen. This is a simple animation, by default this value is 1 which mean that they instantly fade out. If the value is other than 1, there might be a single frame delay before the message goes off screen. 

# Downloading Emote Data


```bash
twitch_log_renderer download emotes twitch bttv ffz --channel one two three  --database my_database.db 
```

requires a default parameter specifying from what providers to fetch emotes **twitch,ffz,bttv**

**--global**
    
    If set downloads the global emotes not specific to a channel

**--channel** 

    [list]
    What channel specific emotes should be downloaded

**--database**

    [string][filepath]
    Path to the database file where we want to put the downloaded emote data

# Downloading Logs

Requires a single parameter with the VoD identifier, that could also be the url to the VoD and *--output* param to pick where to download the file
twitch_log_renderer log <vod_id> --output <out_filename>

# Log Inspect
    This allows for checking the amount of message and durations information
    of a log file, works for all types of log files described

```
twitch_log_renderer inspect <input_log_file>
```


## Color Values

Parameters that allow you to set a color can be in any of the following formats

- RGB Hex(#FFFFFF)
    
    Three hex numbers describing the rgb color we want to use

- ARGB Hex (#FFFFFFFF)
    
    Four hex numbers describing the argb color that we want to use, the first pair is the opacity(alpha)

- the name of the color for example **beige** , **orange** , **red**


## Time Formats
Allowed time formats for the parsed logs are the following:

- Date with time **year/month/day hour:minute:second.microsecond** 

- Time only **hour:minute:second.microsecond**

    

The parameters **start** and **end** that define what portion of the messages should be rendered can be 
in any of the following formats:

- Datetime (same as the definition above)
- Time Only (same as the definition above)
- Time delta **X**h**X**m**X**s.**X**
    
    Defines an time offset with a simple syntax, that doesnt rely on how the defined timestamps in the log 
    are defined. Examples:
        
    ```bash
    1h5m
    ```
    
    ```bash
    5m35s
    ```
    
    ```bash
    5m35s.24
    ```
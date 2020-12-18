from deep_translator import GoogleTranslator
import moviepy.editor as mp
import speech_recognition as sr
import time
import os
import sys
import re

video_path = "C:/Users/Lenovo/Videos/ScreenCapture/raspi/ssh/full4rt0001-27725.mp4"
workspace = sys.path[0] + "/transcriptor_workspace"
audio_path = workspace + "/audio.wav"
language_code = "de-DE"

recognizer = sr.Recognizer()

def get_video_length():
    return mp.VideoFileClip(video_path).duration

def subclip_to_audio(start_time, end_time):
    start = time.process_time()
    clip = mp.VideoFileClip(video_path).subclip(start_time, end_time)
    clip.audio.write_audiofile(audio_path)
    print("Converted video to audio: {}s".format(time.process_time() - start))
    return audio_path

def audio_to_text(audio_path):
    start = time.process_time()
    framerate = 0.1
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        text_data = recognizer.recognize_google(audio_data, language=language_code)
        print("Converted audio to text ({}): {}s".format(language_code, time.process_time() - start))
        return text_data.replace("Team oder Bilder", "Timo the Builder")

def get_audio_segment(offset, duration):
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source, offset=offset, duration=duration)
    return audio

def segment_audio_to_text():
    text = ""
    step_duration = 5
    print("Converting audio to text...")
    start = time.process_time()
    for offset in range(0, int(get_video_length()), step_duration):
        audio = get_audio_segment(offset, step_duration)
        text = text + "\n" + time_formatter(offset) + "," + time_formatter(offset + step_duration) + "\n" + recognize(audio).replace("Team oder Bilder", "Timo the Builder") + "\n"
    print("Converted audio to text ({}): {}s".format(language_code, time.process_time() - start))
    return text

def recognize(audio):
    try:
        return recognizer.recognize_google(audio, language=language_code)
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

def translate_transcript(src_language, dest_language, text_file):
    start = time.process_time()
    with open(text_file) as file:
        lines = file.readlines()
        timestamps, text_src, text_dest = [], ['', ''], []
        for l in range(len(lines)):
            timestamps += re.findall("(00:[0-9]+:[0-9]+.000)(,(00:[0-9]+:[0-9]+.000))", lines[l])
            if l > 1:
                text_src.append(re.sub("(00:[0-9]+:[0-9]+.000,00:[0-9]+:[0-9]+.000)", "", lines[l].replace("\n", "")))
        for l in range(len(text_src)):
            text_dest.append('')
            if text_src[l] != '':
                text_dest[l] = translate_to_language(src_language, dest_language, text_src[l])
            elif text_src[l] == '':
                if text_dest[l - 1] == '' and l > 0:
                    try:
                        address = int((l-2)/3)
                        text_dest[l] = timestamps[address][0] + timestamps[address][1]
                    except:
                        text_dest[l] = ''
    print("Translated {} to {} in sum: {}s".format(src_language, dest_language, time.process_time() - start))
    return text_dest

def translate_to_language(source_language, destination_language, text_to_translate):
    start = time.process_time()
    translator = GoogleTranslator(source='auto', target=destination_language)
    translated = translator.translate(text_to_translate)
    print("Translated {} to {}: {}s".format(source_language, destination_language, time.process_time() - start))
    return translated

def write_to_work_file(file_name, text):
    start = time.process_time()
    file_path = workspace + "/" + file_name + ".lang_trans"
    with open(file_path, "w") as file:
        file.write(text)
    print("Written to {}: {}s (lang_trans)".format(file_name, time.process_time() - start))

def write_to_txt_file(file_name, text):
    start = time.process_time()
    file_path = workspace + "/" + file_name + ".txt"
    with open(file_path, "w") as file:
        file.write(text)
    print("Written to {}: {}s (txt)".format(file_name, time.process_time() - start))

def write_to_trans_file(file_name, text):
    start = time.process_time()
    file_path = workspace + "/" + file_name + ".sbv"
    with open(file_path, "w") as file:
        file.write(text)
    print("Written to {}: {}s (sbv)".format(file_name, time.process_time() - start))

def time_formatter(timestamp):
    return time.strftime("%H:%M:%S.000", time.gmtime(timestamp))

def parse_transcript(text):
    result = ""
    for l in range(len(text)):
        result += text[l] + "\n"
    return result


# first main method
# takes a video, gets the videotext and translates the text to en and es
def write_translations():
    difference = 120
    segments = int(get_video_length() / difference)
    text_de, text_en, text_es = "", "", ""
    for i in range(segments):
        print(i + 1, ". round:")
        text = audio_to_text(subclip_to_audio(i * difference, (i + 1) * difference))
        text_de = text_de + text
        text_en = text_en + translate_to_language("de", "en", text)
        text_es = text_es + translate_to_language("en", "es", text_en)
    print("Last round:")
    text = audio_to_text(subclip_to_audio(segments * difference, -1))
    text_de = text_de + text
    text_en = text_en + translate_to_language("de", "en", text)
    text_es = text_es + translate_to_language("en", "es", text_en)

    print(text_de, "\n\n", text_en, "\n\n", text_es)

    write_to_work_file("text_de", text_de)
    write_to_work_file("text_en", text_en)
    write_to_work_file("text_es", text_es)


if __name__ == "__main__":
    subclip_to_audio(0, -1)
    text_de = segment_audio_to_text()
    write_to_txt_file("text_de", text_de)
    write_to_trans_file("text_en", parse_transcript(translate_transcript("de", "en", workspace + "/text_de.sbv")))
    write_to_trans_file("text_es", parse_transcript(translate_transcript("en", "es", workspace + "/text_en.sbv")))
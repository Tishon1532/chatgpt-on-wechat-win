"""
google voice service
"""
import json
import os

import openai

from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from voice.voice import Voice
import requests
from common import const
import datetime, random

class OpenaiVoice(Voice):
    def __init__(self):
        openai.api_key = conf().get("open_ai_api_key")
        self.language = {
            "en": "english",
            "zh": "chinese",
            "de": "german",
            "es": "spanish",
            "ru": "russian",
            "ko": "korean",
            "fr": "french",
            "ja": "japanese",
            "pt": "portuguese",
            "tr": "turkish",
            "pl": "polish",
            "ca": "catalan",
            "nl": "dutch",
            "ar": "arabic",
            "sv": "swedish",
            "it": "italian",
            "id": "indonesian",
            "hi": "hindi",
            "fi": "finnish",
            "vi": "vietnamese",
            "he": "hebrew",
            "uk": "ukrainian",
            "el": "greek",
            "ms": "malay",
            "cs": "czech",
            "ro": "romanian",
            "da": "danish",
            "hu": "hungarian",
            "ta": "tamil",
            "no": "norwegian",
            "th": "thai",
            "ur": "urdu",
            "hr": "croatian",
            "bg": "bulgarian",
            "lt": "lithuanian",
            "la": "latin",
            "mi": "maori",
            "ml": "malayalam",
            "cy": "welsh",
            "sk": "slovak",
            "te": "telugu",
            "fa": "persian",
            "lv": "latvian",
            "bn": "bengali",
            "sr": "serbian",
            "az": "azerbaijani",
            "sl": "slovenian",
            "kn": "kannada",
            "et": "estonian",
            "mk": "macedonian",
            "br": "breton",
            "eu": "basque",
            "is": "icelandic",
            "hy": "armenian",
            "ne": "nepali",
            "mn": "mongolian",
            "bs": "bosnian",
            "kk": "kazakh",
            "sq": "albanian",
            "sw": "swahili",
            "gl": "galician",
            "mr": "marathi",
            "pa": "punjabi",
            "si": "sinhala",
            "km": "khmer",
            "sn": "shona",
            "yo": "yoruba",
            "so": "somali",
            "af": "afrikaans",
            "oc": "occitan",
            "ka": "georgian",
            "be": "belarusian",
            "tg": "tajik",
            "sd": "sindhi",
            "gu": "gujarati",
            "am": "amharic",
            "yi": "yiddish",
            "lo": "lao",
            "uz": "uzbek",
            "fo": "faroese",
            "ht": "haitian creole",
            "ps": "pashto",
            "tk": "turkmen",
            "nn": "nynorsk",
            "mt": "maltese",
            "sa": "sanskrit",
            "lb": "luxembourgish",
            "my": "myanmar",
            "bo": "tibetan",
            "tl": "tagalog",
            "mg": "malagasy",
            "as": "assamese",
            "tt": "tatar",
            "haw": "hawaiian",
            "ln": "lingala",
            "ha": "hausa",
            "ba": "bashkir",
            "jw": "javanese",
            "su": "sundanese",
            "yue": "cantonese",
        }


    def get_language_value(self, input_lang):
        # 定义原始语言字典

        # 创建一个辅助字典，将语言的缩写和全称都映射到相同的值
        language_map = {}
        for key, value in self.language.items():
            language_map[key] = value
            language_map[value] = value

        # 返回匹配的语言值或未找到时的默认值
        return language_map.get(input_lang.lower(), "Unknown language")


    def voiceToText(self, voice_file):
        logger.debug("[Openai] voice file name={}".format(voice_file))
        try:
            file = open(voice_file, "rb")
            api_base = conf().get("open_ai_api_base")
            url = f'{api_base}/audio/transcriptions'
            headers = {
                'Authorization': 'Bearer ' + conf().get("open_ai_api_key"),
                # 'Content-Type': 'multipart/form-data' # 加了会报错，不知道什么原因
            }
            files = {
                "file": file,
            }
            data = {
                "model": "whisper-1",
                "response_format": "verbose_json",
            }
            response = requests.post(url, headers=headers, files=files, data=data)
            response_data = response.json()
            text = response_data['text']
            language = response_data['language']
            const.LANG = self.get_language_value(language)
            reply = Reply(ReplyType.TEXT, text)
            logger.info("[Openai] voiceToText text={} voice file name={}".format(text, voice_file))
        except Exception as e:
            print(e)
            reply = Reply(ReplyType.ERROR, "我暂时还无法听清您的语音，请稍后再试吧~")
        finally:
            return reply


    def textToVoice(self, text):
        try:
            api_base = conf().get("open_ai_api_base") or "https://api.openai.com/v1"
            url = f'{api_base}/audio/speech'
            headers = {
                'Authorization': 'Bearer ' + conf().get("open_ai_api_key"),
                'Content-Type': 'application/json'
            }
            data = {
                'model': conf().get("text_to_voice_model") or const.TTS_1,
                'input': text,
                'voice': conf().get("tts_voice_id") or "alloy"
            }
            response = requests.post(url, headers=headers, json=data)
            file_name = os.path.join(os.getcwd(), 'tmp', f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(random.randint(0, 1000))}.mp3")
            logger.debug(f"[OPENAI] text_to_Voice file_name={file_name}, input={text}")
            with open(file_name, 'wb') as f:
                f.write(response.content)
            logger.info(f"[OPENAI] text_to_Voice success")
            reply = Reply(ReplyType.VOICE, file_name)
        except Exception as e:
            logger.error(e)
            reply = Reply(ReplyType.ERROR, "遇到了一点小问题，请稍后再问我吧")
        return reply
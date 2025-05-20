from PySide6.QtCore import Signal, QThread
import logging
from translator import Translator

logger = logging.getLogger(__name__)


class TranslatorThread(QThread):
    translation_done = Signal(str, str, dict)
    translation_error = Signal(str)
    translation_progress = Signal(str)  # 流式翻译进度信号

    def __init__(self, translator: Translator):
        super().__init__()
        self.translator = translator
        self.text_to_translate = ""
        self.target_lang = "Chinese"
        self.is_running = False
        self.use_stream = True  # 默认使用流式翻译
        logger.info("Initialization of Translator Thread is completed.")

    def set_text(self, text):
        self.text_to_translate = text

    def set_target_lang(self, target_lang):
        self.target_lang = target_lang

    def set_use_stream(self, use_stream):
        self.use_stream = use_stream

    def run(self):
        self.is_running = True
        try:
            if self.use_stream:
                # 使用流式翻译
                result = self.translator.translate_stream(
                    self.text_to_translate,
                    self.target_lang,
                    callback=self.emit_progress,
                )
                usage = self.translator.get_last_usage()
            else:
                # 使用普通翻译
                result = self.translator.translate(
                    self.text_to_translate, self.target_lang
                )

            # 最后发送translation_done信号
            self.translation_done.emit(self.text_to_translate, result, usage)
        except Exception as e:
            self.translation_error.emit(str(e))
        finally:
            self.is_running = False

    def emit_progress(self, partial_result):
        self.translation_progress.emit(partial_result)

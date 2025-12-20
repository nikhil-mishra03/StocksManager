from langchain_core.callbacks import BaseCallbackHandler
from app.core.logger_config import get_logger

logger = get_logger(__name__)

class ProgressHandler(BaseCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        logger.info("Starting tool: %s", serialized.get("name"))

    def on_tool_end(self, output, **kwargs):
        logger.info("Tool finished")

    def on_llm_new_token(self, token, **kwargs):
        print(token, end="", flush=True)  # or yield to your API stream

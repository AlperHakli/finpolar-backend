from langchain_openai import ChatOpenAI
from project.ai.data_models import OutputParserModel
from dotenv import load_dotenv
# load environmental variables
load_dotenv()
# base model with configurable field named callbacks
basemodel = ChatOpenAI(
    model="gpt-4.1-nano",
    streaming=True,
    temperature=0.0,

)

aimodel = ChatOpenAI(
    model="gpt-4.1-nano",
    streaming = False,
    temperature = 0.0

)


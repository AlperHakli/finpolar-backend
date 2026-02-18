from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# load environmental variables
load_dotenv()
# base model with configurable field named callbacks
basemodel = ChatOpenAI(
    model="gpt-4.1-nano",
    streaming=True,
    temperature=0.0,

)



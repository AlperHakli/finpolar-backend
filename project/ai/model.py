from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_core.runnables import ConfigurableField
from dotenv import load_dotenv

# load environmental variables
load_dotenv()
# base model with configurable field named callbacks
basemodel = ChatOpenAI(
    model="gpt-4.1-nano",
    streaming=True,
    temperature=0.0,



).configurable_fields(
    callbacks=
    ConfigurableField(
        name="Callbacks",
        id="callbacks",
        description="List of callbacks"
    )
)


async def consume_tokens(handler):
    async for token in handler:
        if token:
            print(token , end= " " , flush= True)

async def run_model(model:BaseChatModel  , prompt : str):
    async for _ in model.astream(
        input = prompt
    ):
        ...



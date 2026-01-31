from project.ai.maingraph import app
from project.ai.prompts import SYSTEM_PROMPT
import asyncio
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="messages"),
])



async def run_finpolar():
    final_state = await app.ainvoke(
        {"messages": "Sence THYAO hissesini satın almalımıyım elindeki toolları kullanarak cevap ver"}
    )
    print(f"mesaj contenti: {final_state["messages"][-1].content}")


async def run():
    await run_finpolar()


asyncio.run(run())

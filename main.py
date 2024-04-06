from typing import Optional, Dict
import chainlit.data as cl_data
from datalayer import SQLiteDataLayer
from chainlit.types import ThreadDict
from openai import AsyncClient
import chainlit as cl
import asyncio
import os



# user Authentication
@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin")
    else:
        return None


# Authentication with Microsoft
@cl.oauth_callback
def oauth_callback(provider_id: str, token: str,
    raw_user_data: Dict[str, str],
    default_user: cl.User,) -> Optional[cl.User]:
    return default_user


# setting up custom data layer.
cl_data._data_layer = SQLiteDataLayer("user_database/chainlit.db")


# Initilizing AsyncClient and integrating openai API.
openai_client = AsyncClient(api_key=os.environ.get("OPENAI_API_KEY"))
model_name = "gpt-3.5-turbo"
settings = {
    "temperature": 0.3,
    "max_tokens": 500,
    "top_p": 1,
    "frequency_penalty": 0,
    "presence_penalty": 0,
}


@cl.on_chat_start
async def start_chat():
    cl.user_session.set(
        "message_history", []
    )
    await cl.Avatar(
        name="Gilfoyle",
        url="https://static.wikia.nocookie.net/silicon-valley/images/2/20/Bertram_Gilfoyle.jpg",
    ).send()
    await cl.Avatar(
        name="Dinesh",
        url="https://static.wikia.nocookie.net/silicon-valley/images/e/e3/Dinesh_Chugtai.jpg",
    ).send()


# helper functiom to call openai API.
async def answer_as(name):
    message_history = cl.user_session.get("message_history")
    msg = cl.Message(author=name, content="")
    stream = await openai_client.chat.completions.create(
        model=model_name,
        messages=message_history,
        stream=True,
        **settings,
    )
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)
    await msg.send()


@cl.on_message
async def main(message: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"role": "user", "content": message.content})
    await asyncio.gather(answer_as("Gilfoyle"))


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    message_history = []
    root_messages = [m for m in thread["steps"] if m["parentId"] == 'None']
    for message in root_messages:
        if message["type"] == "user_message":
            message_history.append({"role": "user", "content": message["output"]})
        else:
            message_history.append({"role": "Gilfoyle", "content": message["output"]})
    cl.user_session.set("memory", message_history)
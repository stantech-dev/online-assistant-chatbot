"""Lists all currently available models under the qrok account"""
from groq import Groq

import config
client = Groq(api_key=config.GROQ_API_KEY)
for m in client.models.list().data:
    print(m.id)
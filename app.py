import os
import openai
import ldclient
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig, LDMessage, ProviderConfig
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

import json
import re

app = Flask(__name__)
load_dotenv()

# Initialize clients
ldclient.set_config(Config(os.getenv("LAUNCHDARKLY_SDK_KEY")))  
ld_ai_client = LDAIClient(ldclient.get())  

# openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# use the following client for openrouter / deepseek
openrouter_client = openai.OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

def generate(options=None):
    context = Context.builder('example-user-key').kind('user').name('Sandy').build()

    # !! IMPORTANT !! name of ai configs projects name
    ai_config_key = "compare-models"
    default_value = AIConfig(
        enabled=True,
        model=ModelConfig(name='deepseek-reasoner'),
        messages=[],
    )
    config_value, tracker = ld_ai_client.config(
        ai_config_key,
        context,
        default_value,
)
    model_name = config_value.model.name
    print("CONFIG VALUE: ", config_value)
    print("MODEL NAME: ", model_name)
    print("Trying out % rollout. \n\n")
    
    messages = [] if config_value.messages is None else config_value.messages
    messages_dict=[message.to_dict() for message in messages]

    completion = openrouter_client.chat.completions.create(
            # deepseek chat is not a valid model. have to change to deepseek/deepseek-r1:free from router
            model="deepseek/deepseek-r1:free",
            messages=messages_dict,
        )
    track_success = tracker.track_success()
    print(completion.choices[0].message.content) 
    print("Successful AI Response:")
    return completion


@app.route("/")
def index():
    return render_template("index.html")  

@app.route("/generate", methods=["GET"])
def generate_text():
    response = generate()
    cleaned_text = response.choices[0].message.content
    return jsonify({"text": cleaned_text})


if __name__ == "__main__":
    try:
        app.run(debug=True)
    except KeyboardInterrupt:
        pass
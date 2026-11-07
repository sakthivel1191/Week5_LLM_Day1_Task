from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)
MODEL = "openrouter/free"
prompt = "Explain artificial intelligence in simple words."
def non_streaming():
    print("\nNON-STREAMING")
    start_time = time.time()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300
        )
        end_time = time.time()
        answer = response.choices[0].message.content
        print("Model Name:", response.model)
        print("\nAnswer:")
        print(answer)
        if answer is None:
            print("\nNo answer received!")
            print("Finish Reason:",
                  response.choices[0].finish_reason)
            print("Full Response:", response)
            return ""
        total_time = end_time - start_time
        print("\nFirst output after:",round(total_time, 2), "seconds")
        print("Total time:",round(total_time, 2), "seconds")
        return answer
    except Exception as e:
        print("\nNon-streaming error:", str(e))
        return ""
def streaming():
    print("\nSTREAMING")
    start_time = time.time()
    first_token_time = None
    chunks = []
    finish_reason = None
    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
            stream=True
        )
        print("Streaming Answer:\n")
        for chunk in stream:
            if not chunk.choices:
                continue
            choice = chunk.choices[0]
            content = choice.delta.content
            if choice.finish_reason:
                finish_reason = choice.finish_reason
            if content:
                if first_token_time is None:
                    first_token_time = time.time()
                    print("\nFirst token after:",round(first_token_time - start_time, 2),"seconds\n")
                chunks.append(content)
                print(content, end="", flush=True)
        end_time = time.time()
        final_answer = "".join(chunks)
        if first_token_time is None:
            print("\nNo token received.")
        print("\nFinish Reason:", finish_reason)
        print("Total streaming time:",round(end_time - start_time, 2),"seconds")
        return final_answer
    except Exception as e:
        print("\nStream interrupted!")
        print("Error:", str(e))
        return ""
normal_answer = non_streaming()
streamed_answer = streaming()
print("\nCOMPARISON")
if normal_answer and streamed_answer:
    if normal_answer == streamed_answer:
        print("Both answers match!")
    else:
        print("Answers are different.")
elif not normal_answer:
    print("Non-streaming did not return an answer.")
elif not streamed_answer:
    print("Streaming did not return an answer.")
print("Non-streaming characters:",len(normal_answer))
print("Streaming characters:",len(streamed_answer))

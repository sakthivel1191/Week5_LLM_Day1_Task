import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from SecondHalf.config import(
    OPENAI_MODEL,
    DAILY_BUDGET
)
from SecondHalf.token_tracker import(
    create_database,
    count_tokens,
    check_context_limit,
    calculate_cost,
    save_usage,
    get_today_usage
)
load_dotenv()
API_KEY=os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise ValueError("OpenRouter API key not found")
client=AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY
)
app=FastAPI(
    title="LLM Streaming Application",
    description="OpenRouter Streaming API",
    version="1.0"
)
create_database()
class ChatRequest(BaseModel):
    message:str
def create_messages(message):
    return[
        {
            "role":"user",
            "content":message
        }
    ]
def estimate_request_cost(prompt_tokens,model,max_tokens):
    estimate_cost=calculate_cost(
        prompt_tokens,
        max_tokens,
        model
    )
    return estimate_cost

@app.get("/")
def home():
    return{
        "message":"LLM Streaming API is running"
    }
@app.post("/chat/stream")
async def chat_stream(request:ChatRequest):
    messages=create_messages(request.message)
    try:
        estimate_token=check_context_limit(
            messages,
            OPENAI_MODEL
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
    async def generate():
        stream=None
        try:
            stream=await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                stream=True
            )
            collected_content = []
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    collected_content.append(content)
                    event_data = json.dumps({
                        "content": content
                    })
                    yield f"data: {event_data}\n\n"
            yield "data:[DONE]\n\n"
        except GeneratorExit:
            print("Client disconnected")
            raise
        except Exception as error:
            error_data=json.dumps({
                "error":str(error)
            })
            yield f"event:error\ndata:{error_data}\n\n"
        finally:
            if stream is not None:
                await stream.close()
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":"no-cache",
            "X-Accel-Buffering":"no"
        }
    )

@app.post("/chat")
async def chat(request:ChatRequest):
    messages=create_messages(request.message)
    try:
        estimated_tokens=check_context_limit(
            messages,
            OPENAI_MODEL
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
    try:
        estimated_cost=estimate_request_cost(
            estimated_tokens,
            OPENAI_MODEL,
            500
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
    total_usage=get_today_usage()
    if total_usage["total_cost"]+estimated_cost>DAILY_BUDGET:
        raise HTTPException(
            status_code=429,
            detail="Daily API budget exceeded"
        )
    try:
        response=await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )
    answer=response.choices[0].message.content
    actual_prompt_tokens=response.usage.prompt_tokens
    actual_completion_tokens=response.usage.completion_tokens
    actual_total_tokens=response.usage.total_tokens
    actual_cost=calculate_cost(
        actual_prompt_tokens,
        actual_completion_tokens,
        OPENAI_MODEL
    )
    save_usage(
        OPENAI_MODEL,
        actual_prompt_tokens,
        actual_completion_tokens,
        actual_cost
    )
    return{
        "answer":answer,
        "model":response.model,
        "estimated_input_tokens":estimated_tokens,
        "actual_prompt_tokens":actual_prompt_tokens,
        "completion_tokens":actual_completion_tokens,
        "total_tokens":actual_total_tokens,
        "estimated_cost":round(estimated_cost,8),
        "actual_costs":round(actual_cost,8)
    }

@app.get("/usage")
def usage():
    return get_today_usage()

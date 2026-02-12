import logging
import datetime
from fastapi import FastAPI
import inngest
import inngest.fast_api
from pydantic import BaseModel

# -------------------------------------------------
# Inngest client (ONLY ONE, keep it simple)
# -------------------------------------------------
inngest_client = inngest.Inngest(
    app_id="rag-test-app",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
)

# -------------------------------------------------
# Output model
# -------------------------------------------------
class TestResult(BaseModel):
    message: str
    input_value: str


# -------------------------------------------------
# Simple Inngest test function
# -------------------------------------------------
@inngest_client.create_function(
    fn_id="TEST: Simple Inngest Function",
    trigger=inngest.TriggerEvent(event="test/simple"),
    throttle=inngest.Throttle(
        limit=5,
        period=datetime.timedelta(minutes=1),
    ),
)
async def simple_test_function(ctx: inngest.Context):

    def step_one(ctx: inngest.Context) -> str:
        value = ctx.event.data.get("value", "no value sent")
        print("STEP 1 value:", value)
        return value

    def step_two(value: str) -> TestResult:
        print("STEP 2 processing:", value)
        return TestResult(
            message="Inngest test function executed successfully",
            input_value=value,
        )

    value = await ctx.step.run(
        "step-one",
        lambda: step_one(ctx),
        output_type=str,
    )

    result = await ctx.step.run(
        "step-two",
        lambda: step_two(value),
        output_type=TestResult,
    )

    return result.model_dump()


# -------------------------------------------------
# FastAPI app
# -------------------------------------------------
app = FastAPI()


@app.get("/")
def health():
    return {"status": "ok"}


# -------------------------------------------------
# Serve Inngest with FastAPI
# -------------------------------------------------
inngest.fast_api.serve(
    app,
    inngest_client,
    [simple_test_function],
)

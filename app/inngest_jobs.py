import datetime

import inngest


inngest_client = inngest.Inngest(
    app_id="report-api",
    is_production=False,
)


@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(
        event="test/hello",
    ),
)
async def say_hello(
    ctx: inngest.Context,
):
    await ctx.step.sleep(
        "wait-five-seconds",
        datetime.timedelta(seconds=5),
    )

    return {
        "message":
            "Hello from the background!"
    }


functions = [
    say_hello,
]

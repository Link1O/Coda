from Coda import (
    ShardedClient,
    Intents,
    Event,
    PresenceStatus,
    PollObject,
    Interaction,
    ActionRow,
    Button,
    ButtonStyle,
    StringSelect,
    SelectOption,
    RoleSelect,
    TextInput,
    TextInputStyle,
)

import asyncio

sharded_client = ShardedClient(
    "YOUR_TOKEN",
    intents=Intents.ALL,
    prefix="s!",
    shard_count=2,
    debug=True,
)


async def main():
    await sharded_client.register()

    def bind_handlers(shard):
        @shard.event(Event.READY)
        async def on_ready_event():
            print(f"Shard {shard.shard_id} is ready!")
            await shard.change_presence(
                status=PresenceStatus.DND, value=f"shard no: {shard.shard_id}"
            )

        @shard.event(Event.POLL_END)
        async def on_poll_end_event(poll: PollObject):
            print(f"The poll with the question: '{poll.question}' ended!")

        @shard.slash_command(name="button", description="send a button")
        async def send_button(ctx: Interaction):
            row = ActionRow(
                components=[
                    Button(
                        label="Click Me!",
                        custom_id="click_me",
                        style=ButtonStyle.SUCCESS,
                    )
                ]
            )
            await ctx.respond(content="Here is a button:", components=[row])

        @shard.component("click_me")
        async def on_button_click(ctx: Interaction):
            await ctx.respond(
                content=f"You clicked the button! Message context: {ctx.message.content if ctx.message else 'No message content'}",
                ephemeral=True,
            )

        @shard.slash_command(name="select", description="send a select menu")
        async def send_select(ctx: Interaction):
            row = ActionRow(
                components=[
                    StringSelect(
                        custom_id="select_color",
                        placeholder="Choose a color",
                        options=[
                            SelectOption(
                                label="Red",
                                value="red",
                                description="The color of passion",
                            ),
                            SelectOption(
                                label="Green",
                                value="green",
                                description="The color of nature",
                            ),
                            SelectOption(
                                label="Blue",
                                value="blue",
                                description="The color of the sky",
                            ),
                        ],
                    )
                ]
            )
            await ctx.respond(content="Pick a color:", components=[row])

        @shard.component("select_color")
        async def on_select_color(ctx: Interaction):
            await ctx.respond(content=f"You chose: {ctx.values[0]}", ephemeral=True)

        @shard.slash_command(name="roles", description="select a role")
        async def send_role_select(ctx: Interaction):
            row = ActionRow(
                components=[
                    RoleSelect(
                        custom_id="select_role", placeholder="Select a role to ping"
                    )
                ]
            )
            await ctx.respond(content="Choose a role:", components=[row])

        @shard.component("select_role")
        async def on_role_select(ctx: Interaction):
            await ctx.respond(
                content=f"You selected role ID: {ctx.values[0]}", ephemeral=True
            )

        @shard.slash_command(name="modal", description="open a modal")
        async def open_modal(ctx: Interaction):
            await ctx.modal_response(
                title="Tell us about yourself",
                custom_id="about_me_modal",
                components=[
                    ActionRow(
                        components=[
                            TextInput(
                                custom_id="name",
                                label="What is your name?",
                                placeholder="Pizza steve",
                            )
                        ]
                    ),
                    ActionRow(
                        components=[
                            TextInput(
                                custom_id="bio",
                                label="Tell us more",
                                style=TextInputStyle.PARAGRAPH,
                                placeholder="Im the coolest pizza slice ever!",
                            )
                        ]
                    ),
                ],
            )

        @shard.on_modal_submit("about_me_modal")
        async def on_modal_submit(ctx: Interaction):
            name = ctx.values.get("name")
            bio = ctx.values.get("bio")
            await ctx.respond(content=f"Thanks {name}! Your bio: {bio}", ephemeral=True)

    for shard in sharded_client.shards:
        bind_handlers(shard)
    await sharded_client.connect()


loop = asyncio.new_event_loop()
loop.run_until_complete(main())
loop.run_forever()

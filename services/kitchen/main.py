import asyncio
import json
import aio_pika

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

async def process_order(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        print(f"\n NEW ORDER — Table {data['table_number']} (Order #{data['order_id']})")
        for item in data["items"]:
            print(f"   → {item['quantity']}x {item['name']}")

async def main():
    print("Kitchen service started...")
    await asyncio.sleep(15)  # wait for RabbitMQ to be fully ready

    while True:
        try:
            connection = await aio_pika.connect(RABBITMQ_URL)
            print("Connected to RabbitMQ!")
            channel = await connection.channel()
            queue = await channel.declare_queue("orders", durable=True)
            await queue.consume(process_order)
            print("Listening on 'orders' queue...")
            await asyncio.Future()
        except Exception as e:
            print(f"Error: {e}, retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
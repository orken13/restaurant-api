import asyncio
import json
import aio_pika

RABBITMQ_URL = "amqp://guest:guest@rabbitmq:5672/"

STATUS_MESSAGES = {
    "preparing": "Siparişiniz hazırlanıyor...",
    "ready": "Siparişiniz hazır! Afiyet olsun.",
    "delivered": "Siparişiniz teslim edildi."
}

async def process_notification(message: aio_pika.IncomingMessage):
    async with message.process():
        data = json.loads(message.body)
        status = data["status"]
        msg = STATUS_MESSAGES.get(status, f"Sipariş durumu: {status}")
        print(f"\n NOTIFICATION — Order #{data['order_id']} (Table {data['table_number']})")
        print(f"   → {msg}")

async def main():
    print("Notification service started...")
    await asyncio.sleep(15)  # wait for RabbitMQ to be fully ready

    while True:
        try:
            connection = await aio_pika.connect(RABBITMQ_URL)
            print("Connected to RabbitMQ!")
            channel = await connection.channel()
            queue = await channel.declare_queue("notifications", durable=True)
            await queue.consume(process_notification)
            print("Listening on 'notifications' queue...")
            await asyncio.Future()
        except Exception as e:
            print(f"Error: {e}, retrying in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
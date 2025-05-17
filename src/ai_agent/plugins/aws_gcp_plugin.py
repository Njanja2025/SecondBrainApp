from src.ai_agent.baddy_agent import register_command, log
import os

def handle_send_aws_event():
    try:
        import boto3
        from src.ai_agent.baddy_agent import config
        sns_arn = config.get("aws_sns_arn")
        if sns_arn:
            client = boto3.client("sns")
            client.publish(TopicArn=sns_arn, Message="Test event from Baddy Agent")
            log(f"[AWS] Event sent to SNS: {sns_arn}")
        else:
            log("[AWS] SNS ARN not configured.")
    except Exception as e:
        log(f"[AWS] Failed to send event: {e}")

def handle_send_gcp_event():
    try:
        from google.cloud import pubsub_v1
        from src.ai_agent.baddy_agent import config
        topic = config.get("gcp_pubsub_topic")
        if topic:
            publisher = pubsub_v1.PublisherClient()
            publisher.publish(topic, b"Test event from Baddy Agent")
            log(f"[GCP] Event sent to Pub/Sub: {topic}")
        else:
            log("[GCP] Pub/Sub topic not configured.")
    except Exception as e:
        log(f"[GCP] Failed to send event: {e}")

register_command("send aws event", handle_send_aws_event)
register_command("send gcp event", handle_send_gcp_event) 
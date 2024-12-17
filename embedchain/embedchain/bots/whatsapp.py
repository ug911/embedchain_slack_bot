import argparse
import importlib
import logging
import signal
import sys

from embedchain.helpers.json_serializable import register_deserializable

from .base import BaseBot

logger = logging.getLogger(__name__)


@register_deserializable
class WhatsAppBot(BaseBot):
    def __init__(self):
        try:
            self.flask = importlib.import_module("flask")  # Import Flask for web server functionality
            self.twilio = importlib.import_module("twilio")  # Import Twilio for WhatsApp messaging
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "The required dependencies for WhatsApp are not installed. "
                "Please install with `pip install twilio==8.5.0 flask==2.3.3`"
            ) from None
        super().__init__()

    def handle_message(self, message):
        # Process incoming messages and determine action based on content
        if message.startswith("add "):
            response = self.add_data(message)  # Add data if message starts with 'add '
        else:
            response = self.ask_bot(message)  # Otherwise, query the bot
        return response

    def add_data(self, message):
        # Extract data from the message and add it to the bot's database
        data = message.split(" ")[-1]
        try:
            self.add(data)  # Add the extracted data
            response = f"Added data from: {data}"
        except Exception:
            logger.exception(f"Failed to add data {data}.")
            response = "Some error occurred while adding data."
        return response

    def ask_bot(self, message):
        # Query the bot with the provided message and return the response
        try:
            response = self.query(message)
        except Exception:
            logger.exception(f"Failed to query {message}.")
            response = "An error occurred. Please try again!"
        return response

    def start(self, host="0.0.0.0", port=5000, debug=True):
        # Start the Flask application to handle incoming WhatsApp messages
        app = self.flask.Flask(__name__)

        def signal_handler(sig, frame):
            logger.info("\nGracefully shutting down the WhatsAppBot...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)  # Handle shutdown signal

        @app.route("/chat", methods=["POST"])
        def chat():
            # Handle incoming chat messages from WhatsApp
            incoming_message = self.flask.request.values.get("Body", "").lower()
            response = self.handle_message(incoming_message)  # Process the incoming message
            twilio_response = self.twilio.twiml.messaging_response.MessagingResponse()
            twilio_response.message(response)  # Send the response back to WhatsApp
            return str(twilio_response)

        app.run(host=host, port=port, debug=debug)  # Run the Flask app


def start_command():
    # Command-line interface for starting the WhatsApp bot
    parser = argparse.ArgumentParser(description="EmbedChain WhatsAppBot command line interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind")
    parser.add_argument("--port", default=5000, type=int, help="Port to bind")
    args = parser.parse_args()

    whatsapp_bot = WhatsAppBot()  # Create an instance of the WhatsApp bot
    whatsapp_bot.start(host=args.host, port=args.port)  # Start the bot with specified host and port


if __name__ == "__main__":
    start_command()  # Execute the command-line interface if the script is run directly


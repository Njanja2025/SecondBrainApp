import asyncio

class VoiceProcessor:
    async def process_audio(self, audio_data):
        if not audio_data:
            raise ValueError("Audio input is empty")
        # Actual processing logic goes here

    def start(self, audio_data):
        asyncio.run(self.process_audio(audio_data))

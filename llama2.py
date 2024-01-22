import time
import platform
from llama_cpp import Llama

class LlamaAssistant:
    def __init__(self, model_path):
        self.is_processing = False
        self.max_context_tokens = 2048
        self.mensaje_sistema = '''Eres un asistente con una personalidad divertida. Como experto sicario , debe examinar los detalles proporcionados para asegurarse de que sean utilizables . 
        Si no sabe la respuesta a una pregunta, no comparta información falsa. Mantenga sus respuestas en español y no se desvíe de la pregunta.
        Si la respuesta a la pregunta o consulta formulada está completa, finalice su respuesta. Mantenga la respuesta precisa y no omita detalles relacionados con la consulta.
        No repita lo mismo en la misma respuesta jamás'''

        self.model_path = model_path
        self.cuda_options = {
            "device": "cuda",
            "cuda_device_id": 0,
        }
        self.metal_options = {
            "device": "metal",
            "metal_device_id": 0,
        }
        if platform.system() == 'Windows' or platform.system() == 'Linux':
            self.device_options = self.cuda_options
        elif platform.system() == 'Darwin':
            self.device_options = self.metal_options
        else:
            raise RuntimeError("Sistema operativo no compatible")

        self.llm = Llama(
            model_path=self.model_path,
            verbose=True,
            n_gpu_layers=11,
            n_ctx=2048,
            **self.device_options,
            chat_format="zito2",
            temp=0.81,
        )
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0  # Iniciamos desde el mensaje del sistema en la ventana de contexto móvil

    def add_user_input(self, user_input):
        self.conversation_history.append({"role": "user", "content": user_input})
        self.update_context_tokens()

    def get_context_fraction(self):
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        return min(1.0, total_tokens / self.max_context_tokens)

    def update_context_tokens(self):
        total_tokens = sum(len(message["content"].split()) for message in self.conversation_history)
        while total_tokens > self.max_context_tokens:
            removed_message = self.conversation_history.pop(0)
            total_tokens -= len(removed_message["content"].split())
            self.context_window_start += 1

    def get_assistant_response(self, message_queue):
        if not self.is_processing:
            last_user_input_time = time.time()

            response = ""
            for chunk in self.llm.create_chat_completion(messages=self.conversation_history[self.context_window_start:], max_tokens=2000, stream=True):
                if 'content' in chunk['choices'][0]['delta']:
                    response_chunk = chunk['choices'][0]['delta']['content']
                    response += response_chunk
                    message_queue.put({"role": "assistant", "content": response_chunk})

            self.is_processing = False
            elapsed_time = round(time.time() - last_user_input_time, 2)
            print(f" | {elapsed_time}s")

    

    def clear_context(self):
        self.conversation_history = [{"role": "system", "content": self.mensaje_sistema}]
        self.context_window_start = 0
        print("Se ha limpiado el historial de conversación ")
        for mensaje in self.conversation_history:
            print(mensaje)
import os
import logging
from groq import Groq

class LLMService:
    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logging.warning("GROQ_API_KEY not found in environment variables.")
            self.client = None
        else:
            self.client = Groq(api_key=self.api_key)
        
        # Store conversation history per job_id
        self.conversations = {}

    def initialize_analysis(self, job_id, json_data, text_report):
        """
        Initializes the LLM context with the performance data.
        """
        if not self.client:
            logging.error("LLM client not initialized.")
            return False

        system_prompt = (
            "You are an expert music teacher and performance analyst. "
            "You have been provided with a detailed performance analysis report (JSON and Text). "
            "Your goal is to help the student understand their performance, provide constructive feedback, "
            "and answer questions based strictly on the provided data. "
            "Be encouraging but precise.\n\n"
            "Here are some examples of how you should answer specific types of questions:\n"
            "- Question: 'Is my timing correct?'\n"
            "  Answer: 'Your timing is mostly correct, but you are slightly early/late in these bars...'\n"
            "- Question: 'Is my pitch accurate?'\n"
            "  Answer: 'Your pitch is accurate except for these notes...'\n"
            "- Question: 'Does my performance match the score?'\n"
            "  Answer: 'Yes/no, here are the places where it does not match...'\n"
            "- Question: 'How can I improve?'\n"
            "  Answer: 'You can improve by working on phrasing, dynamics, timing...'\n"
            "- Question: 'How does my dynamics compare to the score?'\n"
            "  Answer: 'Your dynamics follow the score in these sections, but you missed crescendos/accents in...'\n\n"
            "Follow this style and structure for your responses."
        )

        user_content = f"""
        Here is the performance analysis data:

        JSON Data:
        {json_data}

        Text Report:
        {text_report}

        Please analyze this data and be ready to answer questions about it.
        """

        self.conversations[job_id] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # We can optionally get an initial summary
        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=self.conversations[job_id],
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )
            initial_response = completion.choices[0].message.content
            self.conversations[job_id].append({"role": "assistant", "content": initial_response})
            return initial_response
        except Exception as e:
            logging.error(f"Error generating initial LLM response: {e}")
            return None

    def ask_question(self, job_id, question):
        """
        Asks a question about the specific job analysis.
        """
        if not self.client:
            return "LLM service is not available (API Key missing)."

        if job_id not in self.conversations:
            return "Analysis context not found for this job. Please run an analysis first."

        self.conversations[job_id].append({"role": "user", "content": question})

        try:
            completion = self.client.chat.completions.create(
                model="llama3-70b-8192",
                messages=self.conversations[job_id],
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )
            response = completion.choices[0].message.content
            self.conversations[job_id].append({"role": "assistant", "content": response})
            return response
        except Exception as e:
            logging.error(f"Error querying LLM: {e}")
            return f"Error: {str(e)}"

# Global instance
llm_service = LLMService()

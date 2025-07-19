import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import time

# Streamlit app title
st.title("Precise Text Summarizer with Groq and LangChain")

# Input for Groq API key
groq_api_key = st.text_input("Enter your Groq Cloud API key:", type="password")

if groq_api_key:
    # Initialize the Groq LLM with a lighter, faster open-source model (Llama 3 8B)
    llm = ChatGroq(
        groq_api_key=groq_api_key,
        model_name="llama3-8b-8192",  # Faster alternative to 70B; balance of speed and accuracy
        streaming=True  # Enable streaming for perceived speed
    )

    # User input for text to summarize
    input_text = st.text_area("Enter the text to summarize:")

    if st.button("Summarize") and input_text:
        # Define a prompt for precise, comprehensive summaries
        prompt_template = """
        Summarize the following text precisely, ensuring no important points are omitted. 
        Capture all key details, facts, and insights in a concise manner:
        {text}
        """
        prompt = PromptTemplate(input_variables=["text"], template=prompt_template)

        # Check text length to decide chain type (stuff for speed, map-reduce fallback for very long texts)
        if len(input_text) < 8000:  # Use stuff for faster single-pass if under context limit
            chain = load_summarize_chain(
                llm=llm,
                chain_type="stuff",
                prompt=prompt,
                verbose=False  # Disable verbose to reduce overhead
            )
            documents = [Document(page_content=input_text)]  # No splitting needed
            # Generate summary (non-streaming for stuff, but fast)
            with st.spinner("Generating summary..."):
                summary = chain.invoke({"input_documents": documents})["output_text"]
                st.success("Summary:")
                st.write(summary)
        else:
            # Fallback to optimized map-reduce for longer texts
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)  # Larger chunks for fewer calls
            chunks = text_splitter.split_text(input_text)
            documents = [Document(page_content=chunk) for chunk in chunks]
            
            chain = load_summarize_chain(
                llm=llm,
                chain_type="map_reduce",
                map_prompt=prompt,
                combine_prompt=prompt,
                verbose=False  # Disable verbose
            )
            
            # Generate and stream the summary for perceived speed
            with st.spinner("Generating summary..."):
                response_container = st.empty()
                streamed_summary = ""
                # Since map-reduce doesn't stream natively, invoke and stream the final output
                full_summary = chain.invoke({"input_documents": documents})["output_text"]
                # Simulate streaming by chunking the output
                words = full_summary.split()
                for word in words:
                    streamed_summary += word + " "
                    response_container.markdown(streamed_summary)
                    time.sleep(0.05)  # Small delay for streaming effect
                st.success("Summary:")
                st.write(full_summary)
else:
    st.warning("Please enter your Groq API key to proceed.")

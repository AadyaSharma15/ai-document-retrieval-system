import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import os
import pickle
import webbrowser

# Store extracted document content
documents = {}

# Load conversation history    
chat_history = []

# Function to extract text from PDFs
def extract_text_from_pdf(file_path):
    try:
        import fitz
        doc = fitz.open(file_path)
        text = "\n".join([page.get_text() for page in doc])
        return text
    except ImportError:
        messagebox.showerror("Error", "PyMuPDF (fitz) is not installed. Please install it to load PDFs.")
        return ""
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract text from PDF: {str(e)}")
        return ""

# Function to extract text from Word docs
def extract_text_from_docx(file_path):
    try:
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except ImportError:
        messagebox.showerror("Error", "python-docx is not installed. Please install it to load Word documents.")
        return ""
    except Exception as e:
        messagebox.showerror("Error", f"Failed to extract text from Word document: {str(e)}")
        return ""

# Load and process documents
def load_documents():
    global documents
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf"), ("Word Files", "*.docx")])
    if not file_paths:
        return

    documents = {}  # Clear previous documents
    loaded_count = 0
    for file_path in file_paths:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            text = extract_text_from_pdf(file_path)
        elif ext == ".docx":
            text = extract_text_from_docx(file_path)
        else:
            continue

        if text.strip():  # Only add if text is not empty
            documents[file_path] = text
            loaded_count += 1
        else:
            messagebox.showerror("Error", f"Could not extract text from {os.path.basename(file_path)}. The document may be empty, scanned, or in an unsupported format.")

    # Display the extracted text
    results_text.config(state=tk.NORMAL)
    results_text.delete("1.0", tk.END)
    for path, text in documents.items():
        results_text.insert(tk.END, f"📄 {os.path.basename(path)}\n{text}\n\n")
    results_text.config(state=tk.DISABLED)

    if loaded_count > 0:
        messagebox.showinfo("Success", f"Loaded {loaded_count} document(s) successfully!")
    else:
        messagebox.showerror("Error", "No documents could be loaded. Please check the files and required libraries.")

# TF-IDF based search
def search_documents():
    query = search_entry.get()
    if not query:
        messagebox.showerror("Error", "Enter a query to search!")
        return

    if not documents:
        messagebox.showerror("Error", "No documents loaded!")
        return

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        corpus = list(documents.values())
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        query_vector = vectorizer.transform([query])
        
        scores = (tfidf_matrix * query_vector.T).toarray().flatten()
        ranked_docs = sorted(zip(documents.keys(), scores), key=lambda x: x[1], reverse=True)

        results_text.config(state=tk.NORMAL)
        results_text.delete("1.0", tk.END)
        for doc, score in ranked_docs:
            if score > 0:
                results_text.insert(tk.END, f"📄 {os.path.basename(doc)} - Relevance: {score:.4f}\n")
                results_text.insert(tk.END, f"[View More]\n\n")

        results_text.config(state=tk.DISABLED)
    except ImportError:
        messagebox.showerror("Error", "scikit-learn is not installed. Please install it for search functionality.")
    except Exception as e:
        messagebox.showerror("Error", f"Search failed: {str(e)}")

# Function to display full document content
def view_full_document():
    try:
        selected_text = results_text.get(tk.SEL_FIRST, tk.SEL_LAST).strip()
    except tk.TclError:
        selected_text = ""
    
    if not selected_text:
        messagebox.showerror("Error", "Select a document to view!")
        return

    doc_name = selected_text.split(" - ")[0].strip("📄 ")
    for path, content in documents.items():
        if os.path.basename(path) == doc_name:
            doc_window = tk.Toplevel(root)
            doc_window.title(doc_name)
            text_area = scrolledtext.ScrolledText(doc_window, wrap=tk.WORD, width=80, height=25)
            text_area.insert(tk.END, content)
            text_area.pack()
            break

# AI Chat Function

def ask_ai():
    user_input = chat_entry.get().strip()
    if not user_input:
        messagebox.showerror("Error", "Please enter a message to ask!")
        return
    
    try:
        # Open Chrome with Google search for the query
        search_url = f"https://www.google.com/search?q={user_input.replace(' ', '+')}"
        webbrowser.open(search_url)
        
        chat_text.config(state=tk.NORMAL)
        chat_text.insert("end", f"User: {user_input}\nOpened Chrome with search results.\n\n")
        chat_text.config(state=tk.DISABLED)
        chat_history.append({"user": user_input, "ai": "Opened Chrome with search results."})
        chat_entry.delete(0, tk.END)  # Clear the entry after sending
    except Exception as e:
        chat_text.config(state=tk.NORMAL)
        chat_text.insert("end", f"Error: {str(e)}\n\n")
        chat_text.config(state=tk.DISABLED)


# Save chat history
def save_chat():
    with open("chat_history.pkl", "wb") as f:
        pickle.dump(chat_history, f)
    messagebox.showinfo("Success", "Chat history saved!")

# Load chat history
def load_chat():
    global chat_history
    if os.path.exists("chat_history.pkl"):
        with open("chat_history.pkl", "rb") as f:
            chat_history = pickle.load(f)
        chat_text.config(state=tk.NORMAL)
        chat_text.delete("1.0", tk.END)
        for item in chat_history:
            chat_text.insert(tk.END, f"User: {item['user']}\nAI: {item['ai']}\n\n")
        chat_text.config(state=tk.DISABLED)
        messagebox.showinfo("Success", "Chat history loaded!")

# GUI
root = tk.Tk()
root.title("Knowledge Management System")
root.geometry("800x600")

# Search Section
search_label = tk.Label(root, text="Enter your query:")
search_label.pack()
search_entry = tk.Entry(root, width=50)
search_entry.pack()
search_button = tk.Button(root, text="Search", bg="green", fg="white", command=search_documents)
search_button.pack()

# Results Display
results_text = scrolledtext.ScrolledText(root, width=80, height=10, state=tk.DISABLED)
results_text.pack()

# View Document Button
view_doc_button = tk.Button(root, text="View Full Document", command=view_full_document)
view_doc_button.pack()

# Chat Section
chat_label = tk.Label(root, text="Chat with AI:")
chat_label.pack()
chat_entry = tk.Entry(root, width=50)
chat_entry.pack()
chat_button = tk.Button(root, text="Ask AI", bg="blue", fg="white", command=ask_ai)
chat_button.pack()
chat_text = scrolledtext.ScrolledText(root, width=80, height=10, state=tk.DISABLED)
chat_text.pack()

# Load and Save Chat Buttons
save_button = tk.Button(root, text="Save Chat", command=save_chat)
save_button.pack()
load_button = tk.Button(root, text="Load Chat", command=load_chat)
load_button.pack()

# Load Documents Button
load_docs_button = tk.Button(root, text="Load Documents", command=load_documents)
load_docs_button.pack()

root.mainloop()

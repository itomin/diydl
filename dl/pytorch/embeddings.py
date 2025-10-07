#%%
import torch.nn.functional as F
import torch
import torch.optim as optim
from torchtext.datasets.imdb import IMDB
import torchtext
import torchdata
from nltk.corpus import stopwords
from transformers import AutoTokenizer
print("torchtext.__version__", torchtext.__version__)
print("torchdata.__version__", torchdata.__version__)
import re


#%%
train_iter = IMDB(root="./data", split='train')
test_iter = IMDB(root="./data", split='test')

sample = [
"A group of students are studying together at the library.",
"She wrote notes carefully to prepare for the big exam.",
"The teacher encouraged everyone to share their ideas openly.",
"Fresh coffee smells amazing in the morning.",
"He placed a clean mug next to the steaming pot.",
"The café was filled with the sound of clinking cups.",
]


#%%
tokenizer = AutoTokenizer.from_pretrained("google-bert/bert-base-uncased")

#%%
stop_words = set(stopwords.words('english'))
stop_words.update(['.',',',':',';','(',')','#','--','...','"'])
def remove_stopwords(text):
    text = text.lower()
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    return " ".join(filtered_words)


cleaned_words = [ remove_stopwords(s) for s in sample ]
print(cleaned_words)    
inputs = tokenizer(sample, padding="max_length", truncation=True, max_length=20, return_tensors="pt")
tokens = inputs["input_ids"].squeeze(0)  # Remove batch dimension

print(f"Train tensor shape: {tokens.shape}")
# print(f"First sample tokens: {tokens[0][:500]}...")  # Show first 10 tokens


#%%
print(f"Vocabulary size: {tokenizer.vocab_size}")
corpus = F.one_hot(tokens).float()
print(corpus.shape)
print(f"Token IDs: {tokens[0]}")


#%%



# Skip-gram: Create (target_word, aggregated_context) pairs
window_size = 2
target_context_pairs = []

# Process each sentence in the corpus
for sentence_idx in range(corpus.shape[0]):  # For each sentence
    sentence = corpus[sentence_idx]  # Get the one-hot encoded sentence
    
    # For each word position in the sentence
    for word_pos in range(len(sentence)):
        # Get the target word (one-hot vector)
        target_word = sentence[word_pos]
        
        # Skip if this is a padding token (all zeros)
        if target_word.sum() == 0:
            continue
        
        # Initialize context vector (sum of all context words)
        context_vector = torch.zeros_like(target_word)
        context_count = 0
            
        # Find context words within the window
        for context_offset in range(-window_size, window_size + 1):
            context_pos = word_pos + context_offset
            
            # Skip if:
            # - Same position as target word
            # - Outside sentence boundaries
            # - Padding token
            if (context_offset == 0 or 
                context_pos < 0 or 
                context_pos >= len(sentence) or
                sentence[context_pos].sum() == 0):
                continue
                
            context_word = sentence[context_pos]
            context_vector += context_word  # Sum all context words
            context_count += 1
        
        # Only store if we found at least one context word
        if context_count > 0:
            target_context_pairs.append((target_word, context_vector))

print(f"Created {len(target_context_pairs)} target-context pairs")
print(f"Window size: {window_size}")

# Show first few pairs
print(tokens)
print("\nFirst 5 pairs:")
for i, (target, context) in enumerate(target_context_pairs[:5]):
    target_idx = torch.argmax(target).item()
    # Show non-zero elements in context vector
    context_indices = torch.nonzero(context, as_tuple=False).squeeze(-1)
    print(f"Pair {i+1}: target_token_id={target_idx}, context_indices={context_indices.tolist()}")

# Convert to tensors for training
if target_context_pairs:
    target_tensor = torch.stack([pair[0] for pair in target_context_pairs])
    context_tensor = torch.stack([pair[1] for pair in target_context_pairs])
    
    print(f"\nTarget tensor shape: {target_tensor.shape}")
    print(f"Context tensor shape: {context_tensor.shape}")



#%%
class Embedding(torch.nn.Module):
    def __init__(self, vocab_size, embedding_size):
        super(Embedding, self).__init__()
        print(f"Vocab size: {vocab_size}, Embedding size: {embedding_size}")
        self.l1 = torch.nn.Linear(vocab_size, embedding_size, bias=True)
        self.relu = torch.nn.ReLU()
        self.l2 = torch.nn.Linear(embedding_size, vocab_size, bias=True)
        self.softmax = torch.nn.Softmax(dim=1)

    def forward(self, x):
        embedded = self.l1(x)
        h = self.relu(embedded)  # Feed to
        z = self.l2(h)  # Feed to
        return z

#%%
class CBOW_Model(torch.nn.Module):
    def __init__(self, vocab_size, embedding_size):
        super(CBOW_Model, self).__init__()
        self.embeddings = torch.nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embedding_size,
            max_norm=1,
        )
        self.linear = torch.nn.Linear(
            in_features=embedding_size,
            out_features=vocab_size,
        )
    
    def forward(self, inputs_):
        x = self.embeddings(inputs_)
        x = x.mean(axis=1)
        x = self.linear(x)
        return x


# %%
output_size = context_tensor.shape[0]
vocab_size = context_tensor.shape[1]

# Get the correct vocabulary size from the tokenizer
print(f"Vocab size: {vocab_size}")
print(f"Context tensor shape: {context_tensor.shape}")
print(f"Target tensor shape: {target_tensor.shape}")


model = CBOW_Model(vocab_size=vocab_size, embedding_size=2)


n_iterations = 1000
optimizer = optim.SGD(model.parameters(), lr=0.9)
loss = torch.nn.CrossEntropyLoss()

for epoch in range(n_iterations):
    model.train()
    optimizer.zero_grad()
    y_hat = model(context_tensor)
    L = loss(y_hat, target_tensor)
    L.backward()
    optimizer.step()
   
    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {L}")



# print("Prediction")
# with torch.no_grad():
#%%
target_tensor

#%%
corpus = F.one_hot(tokens).float()
vocab_size = corpus.shape[2]

params = list(model.parameters())
word_vectors = params[0].detach()

# Get the actual words from the tokenizer
def get_word_from_token_id(token_id, tokenizer):
    """Convert token ID back to the original word"""
    return tokenizer.decode([token_id])

# Get unique words from cleaned text
unique_words = set()
for sentence in cleaned_words:
    words = sentence.split()
    unique_words.update(words)

print(f"Unique words in cleaned corpus: {len(unique_words)}")
print(f"Cleaned words: {unique_words}")

# Get model parameters
params = list(model.parameters())
embedding_layer = params[0]  # Shape: [vocab_size, embedding_size]
print(f"Embedding layer shape: {embedding_layer.shape}")

# Create word-to-vector mapping by iterating over corpus
word_dict = {}
for word in unique_words:
    # Tokenize the word to get its token ID
    word_tokens = tokenizer.encode(word, add_special_tokens=False)
    if word_tokens:  # If word was successfully tokenized
        token_id = word_tokens[0]  # Take the first token
        
        # Create one-hot vector for this token
        one_hot = torch.zeros(vocab_size)
        one_hot[token_id] = 1.0
        
        # Get word vector by multiplying one-hot with embedding layer
        word_vector = torch.matmul(one_hot, embedding_layer.T)
        
        word_dict[word] = word_vector
        print(f"Word '{word}' -> Token {token_id} -> Vector: {word_vector}")




# %%

#%%
def cosine_similarity(v1, v2):
    return (v1 @ v2) / (torch.norm(v1) * torch.norm(v2))

def most_similar(word, word_dict, top_k=5):
    if word not in word_dict:
        raise ValueError(f"{word} not found in the word dictionary.")

    query_vector = word_dict[word]

    # Calculate cosine similarity with all other words in the dictionary
    similarities = {}
    for other_word, other_vector in word_dict.items():
        if other_word != word:
            similarity = cosine_similarity(query_vector, other_vector)
            similarities[other_word] = similarity

    # Sort the words by similarity in descending order
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

    # Get the top-k most similar words
    top_similar_words = sorted_similarities[:top_k]

    return top_similar_words


# %%
most_similar("mug", word_dict)
# %%
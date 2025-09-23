# %%
import torch
import numpy as np
import math


# %%
tensor = torch.empty([2, 4])
print(tensor)

tensor = torch.rand([2, 4])
print(tensor)

# %%


# %%
tensor = torch.ones([2, 4])
tensor = tensor * 2
print(tensor)

tensor = tensor + tensor * 3
print(tensor)

# %%
torch.manual_seed(42)
m1 = torch.ones([1, 2])
print(m1)

m2 = torch.ones([2, 2]) * 2
print(m2)

print(torch.matmul(m1, m2))


# %%
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))


# %%
# Create tensors with gradient tracking
x = torch.tensor([3.0, 4.0], requires_grad=True)
y = x**2 + 3*x

# # Suppose we want the sum as a "loss"
loss = y.sum()
print(loss)

# # Backpropagation
loss.backward()

print(x.grad)  

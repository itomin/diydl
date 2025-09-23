#%%
import torch.functional as F
import torch
import torch.optim as optim

class Xor(torch.nn.Module):
    def __init__(self):
        super(Xor, self).__init__()
        self.fc1 = torch.nn.Linear(2, 2, bias=True)
        self.sigmoidL1 = torch.nn.Sigmoid()
        self.fc2 = torch.nn.Linear(2, 1, bias=True)
        self.sigmoid = torch.nn.Sigmoid()

    def forward(self, x):
        z = self.fc1(x)
        a = self.sigmoidL1(z)
        z = self.fc2(a)
        a = self.sigmoid(z)
        return a

   



#%%
model = Xor()
x = torch.tensor([[0, 0], [0, 1], [1, 0], [1, 1]]).float()
y = torch.tensor([0,1,1,0]).view(4,1).float()
n_iterations = 10000
optimizer = optim.SGD(model.parameters(), lr=0.9)
loss = torch.nn.MSELoss(reduction='mean')

for epoch in range(n_iterations):
    model.train()
    y_hat = model(x)
    L = loss(y_hat, y)
    L.backward()
    optimizer.step()
    optimizer.zero_grad()
    if epoch % 100 == 0:
        print(f"Epoch {epoch}, Loss: {L}")



print("Prediction")
with torch.no_grad():
    print(model(x))


#%%
for param in model.parameters():
    print(param)
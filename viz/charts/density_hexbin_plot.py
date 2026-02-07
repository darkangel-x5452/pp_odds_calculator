import matplotlib.pyplot as plt

# Scatter + 2D histogram (density)
plt.figure(figsize=(8,6))
hb = plt.hexbin(df['x'], df['y'], gridsize=20, cmap='Blues', mincnt=1)
plt.colorbar(hb, label='Point Count')
plt.xlabel('X')
plt.ylabel('Y')
plt.title('2D Density Hexbin Plot')
plt.show()

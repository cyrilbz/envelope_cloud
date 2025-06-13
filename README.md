# envelope_cloud
Python tool to compute the envelope (alpha shape) of a 3D point cloud, save it and  save some related metrics (volume and area of the alpha shape, projected area on the ground, accuracy of the alpha shape, number of envelopes).


![Screenshot](Screenshot_cloud.png)


![Screenshot](Screenshot_mesh.png)


## Installation

To install and set up the project, follow these steps:

### Prerequisites

Ensure you have the following installed on your system:
- [Git](https://git-scm.com/)
- [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### Step-by-Step Guide

1. **Clone the Repository**

   Open a terminal and run the following command to clone the repository:

   ```bash
   git clone https://github.com/cyrilbz/envelope_cloud.git
   ```
2. ** Move to the directory, create a dedicated Conda environement, and install all requirements**
   ```bash
   cd envelope_cloud

   conda create --name envelope python=3.12.0

   conda activate envelope

   pip install -r requirements.txt
   ```

# envelope_cloud
Python tool to compute the envelope (alpha shape) of a 3D point cloud, save it as .obj, and  save some related metrics (volume and area of the alpha shape, projected area on the ground, accuracy of the alpha shape, number of envelopes) in a csv file.


Only .txt files are supported as inputs for now but this can be improved with some minor modifications.

## Example

Below are two example images demonstrating the functionality of the project:

<div style="display: flex; justify-content: space-around; align-items: center;">
  <div style="text-align: center;">
    <img src="Screenshot_cloud.png" alt="Description of Image 1" width="450"/>
    <p> Input point cloud.</p>
  </div>
  <div style="text-align: center;">
    <img src="Screenshot_mesh.png" alt="Description of Image 2" width="450"/>
    <p> Resulting alpha-shape for a given alpha value, along with the projected surface on the ground. </p>
  </div>
</div>

## Usage
After installing the code (see instructions below), you can run it as you want by modifying the following parameters in the main program (```envelope_cloud.py```)

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

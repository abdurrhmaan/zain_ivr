# IVR Project

This project implements a simple Interactive Voice Response (IVR) system using the Asterisk REST Interface (ARI).

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
    - On Windows: `venv\Scripts\activate`
    - On Unix or MacOS: `source venv/bin/activate`
4. Install the requirements: `pip install -r requirements.txt`
5. Create a `.env` file in the project root with the following content:
   ```
   ARI_USER=your_ari_username
   ARI_PASSWORD=your_ari_password
   ARI_BASE_URL=http://your_asterisk_server:8088
   ```
6. Run the main script: `python main.py`

## Project Structure

- `ivr/`: Main package containing the IVR application code
    - `ari/`: ARI interface
    - `call_flow/`: Call flow logic
    - `config/`: Configuration management
    - `utils/`: Utility functions
- `tests/`: Unit tests
- `config.yml`: Application-specific configuration
- `main.py`: Entry point of the application
- `requirements.txt`: Python dependencies
- `README.md`: Project documentation


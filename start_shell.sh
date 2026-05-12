cd ~/Zenith || exit
source .venv/bin/activate

# load environment variables
if [ -f .env ]; then
  . .env
fi

python src/shell/main.py

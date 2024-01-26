if [ "$(ps  -ef | grep "python3 main.py run" | wc -l)" -lt "2" ]
then
	screen -S discord-bot -X stuff "^C\npython3 main.py run\n"
	echo "Restarted"
fi


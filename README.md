# wave-challenge

# build/run the application

1. navigate to the project directory

2. python3 -m venv auth

3. source auth/bin/activate

4. pip3 install -r requirements.txt

5. python3 -m flask run


# Answers to the questions

1. How did you test that your implementation was correct?

answer: manually test using self-created csv files

2. If this application was destined for a production environment, what would you add or change?

answer: 
  a. go through formal testing phase - unit/integration tests
  b. separate backend and database for better code structure
  c. better validation of user input like avoid corrupted files or malicious code
  d. add better UI and user login/authentication logic
  
3. What compromises did you have to make as a result of the time constraints of this challenge?
  a. implemented rough UI only to fulfill the API requirement
  b. did not separate the backend into different files for easier debugging and view
  c. did not use persistent database, dababase will cleanup all the data once server is down

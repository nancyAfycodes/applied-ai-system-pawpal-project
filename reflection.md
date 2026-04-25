# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- I think the three main core actions to a user is a weekly calender that involves daily actions, depending on the user's schedule, including walking time for the dog, feeding schedule and select pet name; this only applies if the user has more than one dog. Lastly, a check-off list that states if day's tasks have been accomplished
- The classes will include user, with attributes like pet name and schedule and user availability. For the pet, it will include pet name(s), daily tasks like walking, eating, rest time

**b. Design changes**
- Based on my initial design concept, I had two classes, user and pet, with each having attributes such as name, task(s), checkoff list. However, using Claude, it suggested that I have more classes, so as to have each attribute have its class. Thereby making it easier to have more defined attributes. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**
- The consideration was given to priority, depending on task, since certain task(s) can have competing priorities. I decided rather than demote one priority, I will flag it, as a way of keeping track that it needs to be completed. In this way, I'll ensure that high priority tasks like walking the dog as top priority whilst giving the dog its daily vitamins can still be completed at a later time. 

**b. Tradeoffs**
- As I stated above, I flagged priority tasks rather than lower it. This forces the pet owner to weigh each task(s) and determine which, even though important, can be completed at a later time without having any adverse effect to the overall well-being of the pet.However, once I ran pawpal_system.py file, it flagged each tasks due to conflict. Therefore, I had to create a separate section that generates a schedule for each pet, based on owner availability,  rather than a general schedule for each pet.
---

## 3. AI Collaboration

**a. How you used AI**
- I used AI for all aspects of the projects. I started by stating the problem. Then based on my initial thinking asked for improvements. For example, during debugging, I was suppose to get 5 test, but I only had 4/4 test pass. On closer inspection, I realized that in the test file, test_pawpal, it was importing 'Cat' function but it did not use it as part of the test. When I pointed out the error, it was able to correct and have all 5/5 test pass. In conclusion, I didn't rely on AI to make decisions for me, I was able to control the results obtained by stating what was already accomplished, and asking for improvement on logic that I didn't understand especially with error messages like this 'python -m pip install -r requirements.txt
Python was not found; run without arguments to install from the Microsoft Store, or disable this short'. I learned that I had to use 'py' rather than 'python', even though it suggested 'python' while I was debugging, but changed to 'py' once I stated that it wasn't working.

**b. Judgment and verification**
- I was in control of the interaction. For example, in test_pawpal file, it deleted the test for conflict detection, when I asked why, it acknowledge its error and restated the test condition. Since I reviewed  the answers provided, I was able to detect possible errors, thereby making debugging and designing the project a much easier process.

---

## 4. Testing and Verification

**a. What you tested**
- The behaviors tested mainly involved conflicts. My original design was to start with a user with two pets, dog and cat and account for slight differences between the two. For instance, dog/cat need to be fed, however, only dogs require constant activities such as walking. Therefore, I had to account for both pet having a similar schedule, but with varying needs. In addition, I tied each pets' activity to the owner/user. This allowed for combined schedules that may have overlapping tasks. 
- In addition, I added a delete button, which allows the user to delete an incorrect tasks.

**b. Confidence**
- Based on testing done, so far I'll 4/5. Reason being I'll like to include a tracking feature that compares allocated time verses the actual time spent on each assigned task.

---

## 5. Reflection

**a. What went well**
- Overall execution of all sections of the project, and my ability to use AI in a project as well as AI's ability to produce a design that I had suggested.

**b. What you would improve**
- I'll like to include a tracking feature that tracks allocated vs actual time spent on each task for each pet. Generate a graph and use it as a guide to adjust time allotment for each task and pet.

**c. Key takeaway**
- AI is a useful tool that can be used as a companion during large projects, but it still makes mistakes and answers generated should be verified before using as part of a control measure. Using this approach it'll make the project easier to debug and wrong answers removed and/or modified before the project is finished.

## 6. Applied AI System Reflection
*** Disclaimer: this project is a follow-up to the original that involved a a pet care app. Agentic workflow was added to make the project a fully functional AI system app.

**a. What are limitations and biases in your system**
- The app is currently limited to dogs and cats and does not account for other kinds of pets. Furthermore, the user controls the what type of guideline to follow to care for each pet, which maybe skewed towards personal preference rather than suggested guideline for each pet owned. Also, the app assumes that the user(pet owner) has a standard 9-5 day job. It doesn't account for users with shift work or modified work schedules that does not fit the norm. Finally, the app is not dynamic, due to 'mock' mode. In other to function dynamically, it'll need to use an API key; 'mock' mode can be turned off once an API key is present. 

**b. Could your AI be misused and how would you prevent that**
- As with any application, there is possibility for misuse. For example, the user may not document all actions taken for each care, thereby skewing the results produced to show only logged entries. Furthermore, the pet owner may rely heavily on suggestions produced in the app rather than visit a veterinarian, as a way to minimize cost.  While there guardrails, there's nothing stopping the user from having entries related to banned pets. For instance, a user can have a lion or a tiger as a pet, therefore, with its dynamic nature, the app can provide suggestions on care related to lions and tigers, which is intended for a zoologist in a zoo rather than personal pet care.

**c. What surprised you while testing your AI's reliability?**
- I'd think that the main surprise was how it was able to detect the season based on date for each pet care. In addition, the confidence score for each edge case was not expected, even though, I had designed the system to have at least a four out of 5 for each case. 

**d. Describe your collaboration with AI during this project. Identify one instance when the AI gave a helpful suggestion and one instance where its suggestion was flawed or incorrect.**
- One instance AI suggestion was useful was in the original design of the project. For example, on my initial design concept, I had two classes, user and pet, with each having attributes such as name, task(s), checkoff list. However, using Claude, it suggested that I have more classes, so as to have each attribute have its class. Thereby making it easier to have more defined attributes. These suggestions helped in defining additional features such as different breed for dogs and cats. 
- In terms of flawed suggestion, I had to have Claude correct code sections, for example, complexity when it was flagged by Linting to be over the recommended value of 15; this was the main flaw as I had to have versions of each file regenerated to meet linting guidelines. 
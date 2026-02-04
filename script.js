// ----------------------
// DEVELOPMENT STATS
// ----------------------
let stats = {
    attachmentSecurity: 50,
    emotionalRegulation: 50,
    identityClarity: 50,
    socialSupport: 50,
    cognitiveHealth: 50
};

function updateStatsDisplay() {
    document.getElementById("stat-attachment").textContent = stats.attachmentSecurity;
    document.getElementById("stat-emotion").textContent = stats.emotionalRegulation;
    document.getElementById("stat-identity").textContent = stats.identityClarity;
    document.getElementById("stat-social").textContent = stats.socialSupport;
    document.getElementById("stat-cognitive").textContent = stats.cognitiveHealth;
}

// ----------------------
// STAGES AND CHALLENGES WITH LEARNING
// ----------------------
const stages = [
    {
        title: "Prenatal & Infancy",
        theme: "stage-theme-prenatal",
        challenges: [
            {
                text: "A pregnant parent is experiencing high stress. What helps the baby's development most?",
                options: [
                    "Meditation, social support, and healthy nutrition",
                    "Ignoring stress and focusing on work",
                    "Taking medications without consulting a doctor"
                ],
                answer: 0,
                feedback: "Reducing stress through support and healthy habits improves fetal brain development and long-term emotional resilience. Even before birth, maternal health affects the infant’s stress-response system (HPA axis), showing that physical and socioemotional development are interconnected."
            },
            {
                text: "Infant cries frequently. How should a caregiver respond?",
                options: [
                    "Pick up and soothe the infant",
                    "Ignore the cries until they stop",
                    "Only respond if the baby stops crying first"
                ],
                answer: 0,
                feedback: "Consistent, sensitive responses build secure attachment. Infants learn their environment is safe and predictable, supporting emotional regulation, social skills, and brain development."
            }
        ]
    },
    {
        title: "Childhood",
        theme: "stage-theme-childhood",
        challenges: [
            {
                text: "A child refuses to clean up toys. How should a parent respond?",
                options: [
                    "Explain calmly why cleaning is important",
                    "Yell and punish immediately",
                    "Do nothing and let child do as they want"
                ],
                answer: 0,
                feedback: "Supportive, structured parenting teaches responsibility, emotional regulation, and problem-solving. Children develop confidence and understand cause-and-effect relationships through consistent routines."
            },
            {
                text: "Two siblings argue over a toy. What is best?",
                options: [
                    "Guide them to compromise",
                    "Take the toy away from both",
                    "Let them fight it out"
                ],
                answer: 0,
                feedback: "Conflict resolution builds emotional intelligence, communication, and negotiation skills, preparing children for healthy peer relationships."
            }
        ]
    },
    {
        title: "Adolescence",
        theme: "stage-theme-adolescence",
        challenges: [
            {
                text: "Peer pressure encourages risky behavior. How should teen respond?",
                options: [
                    "Refuse politely and choose safe alternatives",
                    "Do what peers say to fit in",
                    "Ignore consequences and rebel"
                ],
                answer: 0,
                feedback: "Positive peer choices strengthen identity clarity and self-confidence. Adolescents develop abstract thinking and moral reasoning, and supportive peers provide a social mirror that reinforces positive identity formation."
            },
            {
                text: "Teen feels self-conscious due to imaginary audience. Best strategy?",
                options: [
                    "Talk openly with supportive friends",
                    "Avoid all social interactions",
                    "Pretend everything is fine and ignore feelings"
                ],
                answer: 0,
                feedback: "Sharing emotions reduces anxiety and helps with socioemotional growth. Understanding the personal fable and imaginary audience helps teens navigate risk-taking and self-perception."
            }
        ]
    },
    {
        title: "Adulthood",
        theme: "stage-theme-adulthood",
        challenges: [
            {
                text: "Stressed at work. How can adult manage stress?",
                options: [
                    "Talk to colleagues/friends, plan tasks",
                    "Ignore stress until it explodes",
                    "Use unhealthy coping like over-eating"
                ],
                answer: 0,
                feedback: "Problem-focused and emotion-focused coping protects emotional health and relationships. Chronic stress can impair memory, concentration, and increase anxiety; using coping strategies reduces these effects."
            },
            {
                text: "Want to maintain cognitive health. What helps?",
                options: [
                    "Continuous learning and social engagement",
                    "Avoid challenges and stick to routine",
                    "Spend all free time on passive entertainment"
                ],
                answer: 0,
                feedback: "Active engagement strengthens cognitive flexibility and resilience. Adults maintain cognitive health by using accumulated knowledge (crystallized intelligence) and staying socially and mentally active."
            }
        ]
    },
    {
        title: "Old Age",
        theme: "stage-theme-oldage",
        challenges: [
            {
                text: "Retired adult wants to stay healthy. Best choice?",
                options: [
                    "Volunteer and maintain friendships",
                    "Stay isolated at home",
                    "Spend money on only passive hobbies"
                ],
                answer: 0,
                feedback: "Social engagement preserves cognitive function and emotional well-being. Active participation in meaningful activities provides purpose and combats loneliness."
            },
            {
                text: "Financial security is limited. Best action?",
                options: [
                    "Use government support wisely and stay active",
                    "Ignore financial planning",
                    "Rely only on family and do nothing"
                ],
                answer: 0,
                feedback: "Financial stability allows independence, continued social engagement, and supports overall well-being in older adulthood."
            }
        ]
    }
];

// ----------------------
// GAME LOGIC
// ----------------------
let currentStage = 0;
let currentChallenge = 0;
let score = 0; // starts at 0
let answered = false;

const introScreen = document.getElementById("intro-screen");
const startBtn = document.getElementById("start-btn");
const gameScreen = document.getElementById("game-screen");
const stageTitle = document.getElementById("stage-title");
const challengeText = document.getElementById("challenge-text");
const choices = [document.getElementById("choice1"), document.getElementById("choice2"), document.getElementById("choice3")];
const feedbackDiv = document.getElementById("feedback");
const progressFill = document.getElementById("progress-fill");
const endScreen = document.getElementById("end-screen");
const finalScore = document.getElementById("final-score");
const outcomeMessage = document.getElementById("outcome-message");
const restartBtn = document.getElementById("restart-btn");
const quitBtn = document.getElementById("quit-btn");

// Create continue button dynamically
const continueBtn = document.createElement("button");
continueBtn.textContent = "Continue";
continueBtn.id = "continue-btn";
continueBtn.style.display = "none";
continueBtn.style.marginTop = "15px";
continueBtn.style.padding = "10px 20px";
continueBtn.style.fontSize = "1em";
document.getElementById("game-screen").appendChild(continueBtn);

// Start game
startBtn.addEventListener("click", () => {
    introScreen.style.display = "none";
    gameScreen.style.display = "block";
    showChallenge();
    updateStatsDisplay();
});

// Show current challenge
function showChallenge() {
    answered = false;
    continueBtn.style.display = "none"; // hide continue button until answered

    const stage = stages[currentStage];
    const challenge = stage.challenges[currentChallenge];

    stageTitle.textContent = stage.title;
    challengeText.textContent = challenge.text;

    const stageInfo = document.getElementById("stage-info");
    stageInfo.className = "";
    stageInfo.classList.add(stage.theme);

    for (let i = 0; i < 3; i++) {
        choices[i].textContent = challenge.options[i];
        choices[i].style.backgroundColor = "white";
        choices[i].style.color = "black";
        choices[i].disabled = false; // re-enable buttons
    }

    feedbackDiv.textContent = "";

    const progress = ((currentStage + currentChallenge / stage.challenges.length) / stages.length) * 100;
    progressFill.style.width = `${progress}%`;
}

// Handle answer selection
choices.forEach((btn, index) => {
    btn.addEventListener("click", () => checkAnswer(index, btn));
});

function checkAnswer(selected, btn) {
    if (answered) return;
    answered = true;

    const challenge = stages[currentStage].challenges[currentChallenge];

    // Show feedback instead of correct answer
    if (selected === challenge.answer) {
        score += 10;
        feedbackDiv.innerHTML = `<strong>✅ Correct!</strong> ${challenge.feedback}`;
    } else {
        feedbackDiv.innerHTML = `<strong>❌ Incorrect.</strong> ${challenge.feedback}`;
    }

    // Update stats
    if (currentStage === 0) stats.attachmentSecurity += (selected === challenge.answer ? 10 : -5);
    if (currentStage === 1) stats.emotionalRegulation += (selected === challenge.answer ? 10 : -5);
    if (currentStage === 2) stats.identityClarity += (selected === challenge.answer ? 10 : -5);
    if (currentStage === 3) stats.socialSupport += (selected === challenge.answer ? 10 : -5);
    if (currentStage === 4) stats.cognitiveHealth += (selected === challenge.answer ? 10 : -5);

    updateStatsDisplay();

    // disable all choices after answering
    choices.forEach(choice => choice.disabled = true);

    // show continue button
    continueBtn.style.display = "inline-block";
}

// Continue to next question
continueBtn.addEventListener("click", () => {
    currentChallenge++;
    if (currentChallenge >= stages[currentStage].challenges.length) {
        currentChallenge = 0;
        currentStage++;
    }
    if (currentStage >= stages.length) {
        endGame();
    } else {
        showChallenge();
    }
});

// End game
function endGame() {
    gameScreen.style.display = "none";
    endScreen.style.display = "block";
    finalScore.textContent = `Your final score: ${score}/100`;

    let message = "";
    if (score >= 80) {
        message = "Excellent! Your choices reflect strong understanding of healthy development. You've built a foundation for resilience and well-being.";
    } else if (score >= 60) {
        message = "Good work! You understand key developmental concepts. Consider reviewing areas like attachment, emotional regulation, or social connections.";
    } else {
        message = "This journey highlights areas for learning. Review how early attachment, supportive parenting, and social connections shape development.";
    }
    outcomeMessage.textContent = message;
}

// Restart
restartBtn.addEventListener("click", () => {
    currentStage = 0;
    currentChallenge = 0;
    score = 0;
    stats = {attachmentSecurity:50, emotionalRegulation:50, identityClarity:50, socialSupport:50, cognitiveHealth:50};
    endScreen.style.display = "none";
    gameScreen.style.display = "block";
    showChallenge();
    updateStatsDisplay();
});

// Quit
quitBtn.addEventListener("click", () => {
    alert("Thank you for playing! Reflect on your choices to understand healthy development.");
});

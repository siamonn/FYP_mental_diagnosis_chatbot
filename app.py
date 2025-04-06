import streamlit as st
import json
from datetime import datetime
import time
import urllib.request
from dotenv import load_dotenv
import os
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Function to communicate with the GPT API
def chat_with_gpt(messages):
    try:
        url = "https://cuhk-api-dev1-apim1.azure-api.net/openai/deployments/gpt-35-turbo/chat/completions?api-version=2023-05-15"

        hdr = {
            # Request headers
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'Ocp-Apim-Subscription-Key': API_KEY,
        }

        # Request body
        data = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        data = json.dumps(data)
        req = urllib.request.Request(url, headers=hdr, data=bytes(data.encode("utf-8")))

        req.get_method = lambda: 'POST'
        response = urllib.request.urlopen(req)
        response_data = json.loads(response.read().decode('utf-8'))
        
        return response_data['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return f"Sorry, I encountered an error while processing your request. Please try again. Error: {str(e)}"

# Function to communicate with the GPT API for report generation
def generate_report_with_gpt(messages):
    max_retries = 2
    retry_count = 0
    last_error = None
    
    while retry_count <= max_retries:
        try:
            url = "https://cuhk-api-dev1-apim1.azure-api.net/openai/deployments/gpt-35-turbo/chat/completions?api-version=2023-05-15"

            hdr = {
                # Request headers
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache',
                'Ocp-Apim-Subscription-Key': API_KEY,  # Use the environment variable API key
            }

            # Request body
            data = {
                "messages": messages,
                "temperature": 0.5,  # Lower temperature for more consistent results
                "max_tokens": 2000  # Increase max tokens for longer reports
            }
            
            data = json.dumps(data)
            req = urllib.request.Request(url, headers=hdr, data=bytes(data.encode("utf-8")))

            req.get_method = lambda: 'POST'
            response = urllib.request.urlopen(req, timeout=90)  # Extended timeout
            response_data = json.loads(response.read().decode('utf-8'))
            
            return response_data['choices'][0]['message']['content']
        except Exception as e:
            last_error = e
            retry_count += 1
            st.warning(f"API error on attempt {retry_count}/{max_retries+1}: {str(e)}. Retrying...")
            time.sleep(2)  # Wait before retrying
    
    # If we get here, all retries failed
    st.error(f"Failed to generate report after {max_retries+1} attempts. Last error: {str(last_error)}")
    raise last_error

# Define assessment tools
ASSESSMENTS = {
    "PHQ-9": {
        "name": "Patient Health Questionnaire-9",
        "description": "Screens for depression",
        "questions": [
            "Little interest or pleasure in doing things?",
            "Feeling down, depressed, or hopeless?",
            "Trouble falling or staying asleep, or sleeping too much?",
            "Feeling tired or having little energy?",
            "Poor appetite or overeating?",
            "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
            "Trouble concentrating on things, such as reading the newspaper or watching television?",
            "Moving or speaking so slowly that other people could have noticed? Or so fidgety or restless that you have been moving a lot more than usual?",
            "Thoughts that you would be better off dead, or thoughts of hurting yourself in some way?"
        ],
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3],
        "interpretation": {
            "0-4": "None-minimal depression",
            "5-9": "Mild depression",
            "10-14": "Moderate depression",
            "15-19": "Moderately severe depression",
            "20-27": "Severe depression"
        }
    },
    "GAD-7": {
        "name": "Generalized Anxiety Disorder-7",
        "description": "Screens for anxiety",
        "questions": [
            "Feeling nervous, anxious, or on edge?",
            "Not being able to stop or control worrying?",
            "Worrying too much about different things?",
            "Trouble relaxing?",
            "Being so restless that it's hard to sit still?",
            "Becoming easily annoyed or irritable?",
            "Feeling afraid, as if something awful might happen?"
        ],
        "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
        "scores": [0, 1, 2, 3],
        "interpretation": {
            "0-4": "Minimal anxiety",
            "5-9": "Mild anxiety",
            "10-14": "Moderate anxiety",
            "15-21": "Severe anxiety"
        }
    },
    "PSS": {
        "name": "Perceived Stress Scale",
        "description": "Measures perceived stress",
        "questions": [
            "Been upset because of something that happened unexpectedly?",
            "Felt unable to control the important things in your life?",
            "Felt nervous and stressed?",
            "Felt confident about your ability to handle personal problems?",
            "Felt that things were going your way?",
            "Found that you could not cope with all the things you had to do?",
            "Been able to control irritations in your life?",
            "Felt that you were on top of things?",
            "Been angered because of things that were outside of your control?",
            "Felt difficulties were piling up so high that you could not overcome them?"
        ],
        "options": ["Never", "Almost never", "Sometimes", "Fairly often", "Very often"],
        "scores": [0, 1, 2, 3, 4],
        "reverse_scored": [4, 5, 7, 8],  # 0-indexed questions that are reverse scored
        "interpretation": {
            "0-13": "Low stress",
            "14-26": "Moderate stress",
            "27-40": "High perceived stress"
        }
    },
    "PCL-5": {
        "name": "PTSD Checklist for DSM-5",
        "description": "Screens for PTSD symptoms",
        "questions": [
            "Repeated, disturbing, and unwanted memories of the stressful experience?",
            "Repeated, disturbing dreams of the stressful experience?",
            "Suddenly feeling or acting as if the stressful experience were actually happening again (as if you were actually back there reliving it)?",
            "Feeling very upset when something reminded you of the stressful experience?",
            "Having strong physical reactions when something reminded you of the stressful experience (for example, heart pounding, trouble breathing, sweating)?",
            "Avoiding memories, thoughts, or feelings related to the stressful experience?",
            "Avoiding external reminders of the stressful experience (for example, people, places, conversations, activities, objects, or situations)?",
            "Trouble remembering important parts of the stressful experience?",
            "Having strong negative beliefs about yourself, other people, or the world (for example, having thoughts such as: I am bad, there is something seriously wrong with me, no one can be trusted, the world is completely dangerous)?",
            "Blaming yourself or someone else for the stressful experience or what happened after it?",
            "Having strong negative feelings such as fear, horror, anger, guilt, or shame?",
            "Loss of interest in activities that you used to enjoy?",
            "Feeling distant or cut off from other people?",
            "Trouble experiencing positive feelings (for example, being unable to feel happiness or have loving feelings for people close to you)?",
            "Irritable behavior, angry outbursts, or acting aggressively?",
            "Taking too many risks or doing things that could cause you harm?",
            "Being 'superalert' or watchful or on guard?",
            "Feeling jumpy or easily startled?",
            "Having difficulty concentrating?",
            "Trouble falling or staying asleep?"
        ],
        "options": ["Not at all", "A little bit", "Moderately", "Quite a bit", "Extremely"],
        "scores": [0, 1, 2, 3, 4],
        "interpretation": {
            "0-31": "Below threshold for PTSD",
            "32-80": "Probable PTSD - clinical assessment recommended"
        }
    },
    "BHS": {
        "name": "Beck Hopelessness Scale",
        "description": "Measures negative attitudes about the future",
        "questions": [
            "I look forward to the future with hope and enthusiasm.",
            "I might as well give up because there is nothing I can do about making things better for myself.",
            "When things are going badly, I am helped by knowing that they cannot stay that way forever.",
            "I can't imagine what my life would be like in ten years.",
            "I have enough time to accomplish the things I want to do.",
            "In the future, I expect to succeed in what concerns me most.",
            "My future seems dark to me.",
            "I happen to be particularly lucky, and I expect to get more of the good things in life than the average person.",
            "I just can't get the breaks, and there's no reason I will in the future.",
            "My past experiences have prepared me well for the future.",
            "All I can see ahead of me is unpleasantness rather than pleasantness.",
            "I don't expect to get what I really want.",
            "When I look ahead to the future, I expect I will be happier than I am now.",
            "Things just won't work out the way I want them to.",
            "I have great faith in the future.",
            "I never get what I want, so it's foolish to want anything.",
            "It's very unlikely that I will get any real satisfaction in the future.",
            "The future seems vague and uncertain to me.",
            "I can look forward to more good times than bad times.",
            "There's no use in really trying to get anything I want because I probably won't get it."
        ],
        "options": ["True", "False"],
        "scores": [1, 0],
        "reverse_scored": [0, 2, 4, 5, 7, 9, 12, 14, 18],  # 0-indexed questions that are reverse scored
        "interpretation": {
            "0-3": "Minimal hopelessness",
            "4-8": "Mild hopelessness",
            "9-14": "Moderate hopelessness",
            "15-20": "Severe hopelessness"
        }
    }
}

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_state" not in st.session_state:
    st.session_state.chat_state = "screening"  # Options: screening, assessment, report

if "diagnosis" not in st.session_state:
    st.session_state.diagnosis = {
        "possible_conditions": [],
        "assessment_results": {},
        "final_diagnosis": "",
        "recommendations": ""
    }

if "current_assessment" not in st.session_state:
    st.session_state.current_assessment = None

if "assessment_responses" not in st.session_state:
    st.session_state.assessment_responses = {}

if "assessment_index" not in st.session_state:
    st.session_state.assessment_index = 0

# Function to get healthcare recommendations based on assessment results
def get_healthcare_recommendation(assessment_name, score, interpretation):
    if assessment_name == "Patient Health Questionnaire-9":
        if score >= 10:  # Moderate, moderately severe, or severe depression
            return "Based on your assessment score, it's recommended that you speak with a healthcare provider such as a primary care physician or mental health professional. Your symptoms suggest you might benefit from professional support."
        else:  # Minimal or mild depression
            return "Your symptoms appear to be mild. Self-care strategies like regular exercise, maintaining social connections, and good sleep habits may help. However, if symptoms persist or worsen, please consult a healthcare provider."
    
    elif assessment_name == "Generalized Anxiety Disorder-7":
        if score >= 10:  # Moderate or severe anxiety
            return "Your assessment suggests significant anxiety symptoms. It's recommended that you consult with a healthcare provider for a proper evaluation and discussion of treatment options."
        else:  # Minimal or mild anxiety
            return "Your anxiety symptoms appear to be mild. Stress management techniques such as mindfulness, deep breathing, and regular physical activity may be helpful. If symptoms persist or worsen, please seek professional help."
    
    elif assessment_name == "PTSD Checklist for DSM-5":
        if score >= 32:  # Above threshold for PTSD
            return "Your assessment score suggests you may be experiencing significant PTSD symptoms. It's strongly recommended that you speak with a mental health professional specializing in trauma for proper evaluation and support."
        else:  # Below threshold
            return "Your symptoms are below the clinical threshold for PTSD. However, if you're experiencing distress related to a traumatic event, speaking with a mental health professional can still be beneficial."
    
    elif assessment_name == "Perceived Stress Scale":
        if score >= 27:  # High stress
            return "Your assessment indicates high levels of perceived stress. Consider consulting with a healthcare provider about stress management strategies and to rule out stress-related health issues."
        else:  # Low to moderate stress
            return "Your stress levels appear to be manageable. Continuing self-care practices like regular exercise, adequate sleep, and relaxation techniques is recommended. If stress begins to interfere with daily functioning, consider seeking professional support."
    
    elif assessment_name == "Beck Hopelessness Scale":
        if score >= 9:  # Moderate to severe hopelessness
            return "Your assessment indicates significant feelings of hopelessness. It's important to speak with a mental health professional soon, especially if you're having thoughts of harming yourself."
        else:  # Minimal to mild hopelessness
            return "Your feelings of hopelessness appear to be mild. Engaging in positive activities, maintaining social connections, and practicing self-compassion may help. If these feelings persist or worsen, please seek professional help."
    
    else:
        return "Based on your assessment results, it's always a good idea to discuss your mental health with a qualified healthcare provider during your regular check-ups."

# Function for the screening agent
def screening_agent(user_input):
    screening_prompt = [
        {"role": "system", "content": """You are a mental health screening specialist. 
        Your task is to have a conversation with the patient to identify potential mental health issues.
        Ask about the patient's name, age, gender.
        Ask about their feelings, experiences and symptoms.
        Based on their responses, identify potential mental health conditions they might have (normal, depression, anxiety, ptsd, hopelessness, stress), for the conditions out of the list,e.g schizophrenia,  hallucinations, etc, please say "the chatbot can only detect the conditions of depression, anxiety, ptsd, hopelessness and stress,
         for the other conditions, please seek a professional help"
        think about the reason of the patient's systomps, if the reason is not related to the mental health,e.g schizophrenia, please say "the chatbot can only detect the conditions of depression, anxiety, ptsd, hopelessness and stress,
         for the other conditions, please seek a professional help"
        or determine if they appear mentally healthy. Ask follow-up questions to gather more information that helps you determine if they have a mental health condition.
        Once you have enough information, you do not need to ask any more questions, just end the conversation with a JSON output in this format:
        {"screening_complete": true, "possible_conditions": ["condition1", "condition2"], "notes": "brief notes on observations"}
        If the patient appears mentally healthy with no significant issues, include "normal" in the possible_conditions list.
        IMPORTANT: When sending the JSON, DO NOT include any other text before or after the JSON - only send the JSON object itself.

        Do not recommend any things to patients and focus on the screening, unless you detect a URGENT SAFETY CONCERN, please recommend the following:
        1. **If you are in an immediately dangerous situation (such as on a rooftop, bridge, or with means of harm):**
        - Move to a safe location immediately
        - Call emergency services: 999
        - Stay on the line with emergency services

        2. **For immediate support:**
        - Go to your nearest emergency room/A&E department
        - Call The Samaritans hotline (Multilingual): (852) 2896 0000
        - Call Suicide Prevention Service hotline (Cantonese): (852) 2382 0000

        **Are you currently in a safe location?** If not, please seek immediate help using the emergency contacts above.
        and ask if the patient would like to continue with our assessment, or would they prefer I provide more resources or support options?
        
         """}
        
    ]
    
    # Add chat history
    for message in st.session_state.messages:
        if message["role"] in ["user", "assistant"]:
            screening_prompt.append(message)
    
    # Add current user input
    screening_prompt.append({"role": "user", "content": user_input})
    
    # Get response from GPT
    response = chat_with_gpt(screening_prompt)
    
    # Check if response contains JSON
    try:
        # Try to find JSON in the response
        import re
        json_match = re.search(r'({.*})', response.replace('\n', ' '))
        if json_match:
            json_str = json_match.group(1)
            result = json.loads(json_str)
            
            if result.get("screening_complete"):
                st.session_state.diagnosis["possible_conditions"] = result.get("possible_conditions", [])
                st.session_state.chat_state = "assessment"
                
                # Add a user-friendly response to chat history instead of the JSON
                user_friendly_message = "Thank you for sharing your experiences with me. Based on what you've told me, I have a better understanding of your situation."
                st.session_state.messages.append({"role": "assistant", "content": user_friendly_message})
                
                # Prepare for assessment if needed
                if "normal" not in result.get("possible_conditions", []) and result.get("possible_conditions"):
                    # Determine assessment needed based on possible conditions
                    conditions = result.get("possible_conditions", [])
                    conditions = [c.lower() for c in conditions]  # Convert all to lowercase for easier comparison
                    
                    # Create a list to store the order of assessments
                    assessment_order = []
                    
                    # Check for conditions in priority order
                    if "depression" in conditions:
                        assessment_order.append("PHQ-9")
                    if "anxiety" in conditions:
                        assessment_order.append("GAD-7")
                    if "ptsd" in conditions:
                        assessment_order.append("PCL-5")
                    if "hopelessness" in conditions:
                        assessment_order.append("BHS")
                    if "stress" in conditions:
                        assessment_order.append("PSS")
                    
                    # If no specific assessments matched but conditions exist, provide general advice
                    if not assessment_order:
                        return "Based on your responses, it's important to speak with a healthcare provider for a proper evaluation and discussion of treatment options."
                    
                    # Start with the first assessment
                    st.session_state.current_assessment = assessment_order[0]
                    
                    # Save all identified conditions to ensure subsequent assessments are conducted
                    st.session_state.diagnosis["possible_conditions"] = conditions
                    
                    # Notify user of transition to assessment
                    assessment_intro = f"Based on our conversation, I'd like to conduct a {ASSESSMENTS[st.session_state.current_assessment]['name']} assessment to better understand your symptoms. Let's begin with the first question."
                    st.session_state.messages.append({"role": "assistant", "content": assessment_intro})
                    return assessment_intro
                else:
                    # If patient appears normal, skip to report
                    st.session_state.chat_state = "report"
                    return generate_report()
            else:
                # Not ready for assessment yet, just add the normal response
                st.session_state.messages.append({"role": "assistant", "content": response})
                return response
    except Exception as e:
        # If JSON parsing fails, just show the normal response
        st.error(f"Error parsing screening result: {str(e)}")
        st.session_state.messages.append({"role": "assistant", "content": response})
        return response
    
    # No JSON detected, just add the response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
    return response

# Function to handle assessment
def assessment_agent():
    current = st.session_state.current_assessment
    assessment_data = ASSESSMENTS[current]
    
    # Ensure assessment index is reset when switching to a new assessment
    if "last_assessment" not in st.session_state:
        st.session_state.last_assessment = current
    elif st.session_state.last_assessment != current:
        st.session_state.assessment_index = 0  # Reset index for new assessment
        st.session_state.last_assessment = current
    
    if st.session_state.assessment_index < len(assessment_data["questions"]):
        # Display current question
        question = assessment_data["questions"][st.session_state.assessment_index]
        
        # Only display the question in the UI, don't add to message history yet
        st.markdown(f"**Question {st.session_state.assessment_index + 1}:** {question}")
        
        # Create columns for options
        cols = st.columns(len(assessment_data["options"]))
        
        # Display options as buttons
        for i, col in enumerate(cols):
            if col.button(assessment_data["options"][i], key=f"option_{i}_{st.session_state.assessment_index}_{current}"):
                # First, add the current question to message history
                st.session_state.messages.append({"role": "assistant", "content": f"Question {st.session_state.assessment_index + 1}: {question}"})
                
                # Save response
                if current not in st.session_state.assessment_responses:
                    st.session_state.assessment_responses[current] = []
                
                # Calculate score (handle reverse scoring if needed)
                score = assessment_data["scores"][i]
                if "reverse_scored" in assessment_data and st.session_state.assessment_index in assessment_data.get("reverse_scored", []):
                    if current == "BHS":
                        # For BHS, reverse is just flipping 0 and 1
                        score = 1 - score
                    else:
                        # For other scales with more options
                        score = assessment_data["scores"][-i-1]
                
                st.session_state.assessment_responses[current].append(score)
                
                # Record user's answer
                st.session_state.messages.append({"role": "user", "content": f"My answer: {assessment_data['options'][i]}"})
                
                # Move to next question immediately
                st.session_state.assessment_index += 1
                
                # Force an immediate rerun for better responsiveness
                st.rerun()
                
                # If all questions answered, calculate results
                if st.session_state.assessment_index >= len(assessment_data["questions"]):
                    # Calculate total score
                    total_score = sum(st.session_state.assessment_responses[current])
                    
                    # Determine interpretation
                    interpretation = ""
                    for score_range, interp in assessment_data["interpretation"].items():
                        min_score, max_score = map(int, score_range.split("-"))
                        if min_score <= total_score <= max_score:
                            interpretation = interp
                            break
                    
                    # Save results
                    st.session_state.diagnosis["assessment_results"][current] = {
                        "score": total_score,
                        "interpretation": interpretation
                    }
                    
                    # Report results to user with healthcare recommendation and disclaimer
                    result_message = f"""Assessment complete: {assessment_data['name']}
Score: {total_score}
Interpretation: {interpretation}

**Healthcare Recommendation:**
{get_healthcare_recommendation(assessment_data['name'], total_score, interpretation)}

**Important Disclaimer:**
This assessment is a screening tool and not a clinical diagnosis. The chatbot cannot provide a real medical diagnosis and is not a substitute for professional healthcare. Please consult with a qualified healthcare provider for proper evaluation and treatment."""
                    
                    st.session_state.messages.append({"role": "assistant", "content": result_message})
                    
                    # Check if more assessments needed based on possible conditions
                    possible_conditions = st.session_state.diagnosis["possible_conditions"]
                    
                    # Create a priority list of assessments to conduct in sequence
                    assessment_priorities = []
                    
                    # Populate the priority list based on conditions
                    if "depression" in possible_conditions:
                        if "PHQ-9" not in st.session_state.diagnosis["assessment_results"] and current != "PHQ-9":
                            assessment_priorities.append("PHQ-9")
                            
                    if "anxiety" in possible_conditions:
                        if "GAD-7" not in st.session_state.diagnosis["assessment_results"] and current != "GAD-7":
                            assessment_priorities.append("GAD-7")
                            
                    if "ptsd" in possible_conditions:
                        if "PCL-5" not in st.session_state.diagnosis["assessment_results"] and current != "PCL-5":
                            assessment_priorities.append("PCL-5")
                            
                    if "hopelessness" in possible_conditions:
                        if "BHS" not in st.session_state.diagnosis["assessment_results"] and current != "BHS":
                            assessment_priorities.append("BHS")
                            
                    if "stress" in possible_conditions:
                        if "PSS" not in st.session_state.diagnosis["assessment_results"] and current != "PSS":
                            assessment_priorities.append("PSS")
                    
                    # Get the next assessment if any remain
                    if assessment_priorities:
                        next_assessment = assessment_priorities[0]
                        st.session_state.current_assessment = next_assessment
                        st.session_state.assessment_index = 0
                        next_assessment_intro = f"Let's also conduct a {ASSESSMENTS[next_assessment]['name']} assessment. Let's begin with the first question."
                        st.session_state.messages.append({"role": "assistant", "content": next_assessment_intro})
                        
                        # Force an immediate rerun for better responsiveness
                        st.rerun()
                        
                        return next_assessment_intro
                    else:
                        # Move to report generation if no more assessments needed
                        st.session_state.chat_state = "report"
                        transition_message = """Thank you for completing the assessments. I'll now generate a comprehensive report based on our conversation and your assessment results.

While I can provide a summary of your assessment results, please remember that these assessments are screening tools only and not a substitute for professional medical diagnosis. 

Based on your results, the report will include recommendations about whether you should consult with a healthcare provider or can continue with self-care strategies at home.

I'm generating your report now..."""
                        st.session_state.messages.append({"role": "assistant", "content": transition_message})
                        
                        # Force an immediate rerun
                        st.rerun()
                        
                        return generate_report()
        
        return None
    
    # If we get here, all questions in the current assessment are completed
    if st.session_state.assessment_index >= len(assessment_data["questions"]):
        # Calculate total score
        total_score = sum(st.session_state.assessment_responses[current])
        
        # Determine interpretation
        interpretation = ""
        for score_range, interp in assessment_data["interpretation"].items():
            min_score, max_score = map(int, score_range.split("-"))
            if min_score <= total_score <= max_score:
                interpretation = interp
                break
        
        # Save results
        st.session_state.diagnosis["assessment_results"][current] = {
            "score": total_score,
            "interpretation": interpretation
        }
        
        # Report results to user with healthcare recommendation and disclaimer
        result_message = f"""Assessment complete: {assessment_data['name']}
Score: {total_score}
Interpretation: {interpretation}

**Healthcare Recommendation:**
{get_healthcare_recommendation(assessment_data['name'], total_score, interpretation)}

**Important Disclaimer:**
This assessment is a screening tool and not a clinical diagnosis. The chatbot cannot provide a real medical diagnosis and is not a substitute for professional healthcare. Please consult with a qualified healthcare provider for proper evaluation and treatment."""
        
        st.session_state.messages.append({"role": "assistant", "content": result_message})
        
        # Check if more assessments needed based on possible conditions
        possible_conditions = st.session_state.diagnosis["possible_conditions"]
        
        # Create a priority list of assessments to conduct in sequence
        assessment_priorities = []
        
        # Populate the priority list based on conditions
        if "depression" in possible_conditions:
            if "PHQ-9" not in st.session_state.diagnosis["assessment_results"] and current != "PHQ-9":
                assessment_priorities.append("PHQ-9")
                
        if "anxiety" in possible_conditions:
            if "GAD-7" not in st.session_state.diagnosis["assessment_results"] and current != "GAD-7":
                assessment_priorities.append("GAD-7")
                
        if "ptsd" in possible_conditions:
            if "PCL-5" not in st.session_state.diagnosis["assessment_results"] and current != "PCL-5":
                assessment_priorities.append("PCL-5")
                
        if "hopelessness" in possible_conditions:
            if "BHS" not in st.session_state.diagnosis["assessment_results"] and current != "BHS":
                assessment_priorities.append("BHS")
                
        if "stress" in possible_conditions:
            if "PSS" not in st.session_state.diagnosis["assessment_results"] and current != "PSS":
                assessment_priorities.append("PSS")
        
        # Get the next assessment if any remain
        if assessment_priorities:
            next_assessment = assessment_priorities[0]
            st.session_state.current_assessment = next_assessment
            st.session_state.assessment_index = 0
            next_assessment_intro = f"Let's also conduct a {ASSESSMENTS[next_assessment]['name']} assessment. Let's begin with the first question."
            st.session_state.messages.append({"role": "assistant", "content": next_assessment_intro})
            
            # Force an immediate rerun for better responsiveness
            st.rerun()
            
            return next_assessment_intro
        else:
            # Move to report generation if no more assessments needed
            st.session_state.chat_state = "report"
            transition_message = """Thank you for completing the assessments. I'll now generate a comprehensive report based on our conversation and your assessment results.

While I can provide a summary of your assessment results, please remember that these assessments are screening tools only and not a substitute for professional medical diagnosis. 

Based on your results, the report will include recommendations about whether you should consult with a healthcare provider or can continue with self-care strategies at home.

I'm generating your report now..."""
            st.session_state.messages.append({"role": "assistant", "content": transition_message})
            
            # Force an immediate rerun
            st.rerun()
            
            return generate_report()
    
    return None

# Function to generate a diagnosis report
def generate_report():
    try:
        # Check if any assessments have been completed
        if not st.session_state.diagnosis["assessment_results"]:
            warning_message = "No assessments have been completed yet. The report may be limited."
            st.warning(warning_message)
        
        report_prompt = [
            {"role": "system", "content": """You are a mental health report specialist.
            Generate a comprehensive mental health diagnosis report based on the screening conversation and assessment results.
            Format the report professionally with clearly labeled sections for:
            1. Patient Information (extract from conversation)
            2. Presenting Symptoms (summarize symptoms mentioned in conversation)
            3. Assessment Results (detailed results of each assessment with scores and interpretations)
            4. Diagnosis (provide a tentative diagnosis based on assessments and symptoms)
            5. Recommendations (suggest appropriate treatments or further evaluations)
            6. Disclaimer (IMPORTANT: Include a clear and prominent disclaimer section at the end)
            
            Be specific, professional, and compassionate. Include the date in the report header.
            If multiple conditions are present, address each one separately in the diagnosis and recommendations.
            Focus on evidence-based information and avoid making definitive claims without appropriate qualification.
            
            In your recommendations section, clearly state whether the patient should:
            - Seek professional medical attention soon based on assessment results
            - Consider consulting with a healthcare provider
            - Continue self-care strategies at home
            
            In the disclaimer section, include the following text verbatim:
            "IMPORTANT DISCLAIMER: This report is generated by an AI assistant and is not a clinical diagnosis. 
            The assessment tools used are screening instruments only and do not replace a proper evaluation by a qualified healthcare professional.
            This report is not a substitute for professional medical advice, diagnosis, or treatment.
            If you're experiencing severe symptoms or having thoughts of harming yourself or others, please seek immediate medical attention or contact a crisis helpline."
            """
            }
        ]
        
        # Add chat history
        conversation_data = []
        for message in st.session_state.messages:
            if message["role"] in ["user", "assistant"]:
                # Skip assessment questions and responses to focus on the narrative conversation
                if not (message["content"].startswith("Question") or message["content"].startswith("My answer:")):
                    conversation_data.append(message)
        
        # Add filtered conversation to the prompt
        for message in conversation_data:
            report_prompt.append(message)
        
        # Add assessment results in detail
        assessment_results = "Assessment Results Summary:\n"
        for assessment, result in st.session_state.diagnosis["assessment_results"].items():
            assessment_data = ASSESSMENTS[assessment]
            assessment_results += f"- {assessment_data['name']} ({assessment_data['description']})\n"
            assessment_results += f"  Score: {result['score']}\n"
            assessment_results += f"  Interpretation: {result['interpretation']}\n\n"
        
        # Add possible conditions identified during screening
        conditions = ", ".join(st.session_state.diagnosis["possible_conditions"]) if st.session_state.diagnosis["possible_conditions"] else "No specific conditions identified"
        assessment_results += f"Possible conditions identified during screening: {conditions}\n\n"
        
        report_prompt.append({"role": "user", "content": f"Generate a comprehensive diagnosis report based on our conversation and the following assessment results:\n{assessment_results}\nInclude today's date ({datetime.now().strftime('%B %d, %Y')}) in the report header."})
        
        # Get response from GPT using the enhanced report generation function
        report = generate_report_with_gpt(report_prompt)
        
        # Save report to session state
        st.session_state.messages.append({"role": "assistant", "content": report})
        
        return report
    except Exception as e:
        error_message = f"Error generating report: {str(e)}"
        st.error(error_message)
        
        # Provide a fallback report to ensure something is returned
        fallback_report = f"""
        # Mental Health Report
        
        ## Date: {datetime.now().strftime('%B %d, %Y')}
        
        ### Assessment Results
        {assessment_results}
        
        ### Note
        There was an issue generating the complete report. Please try restarting the conversation or contact support.
        
        This report is not a substitute for professional psychiatric evaluation. Please consult with a mental health professional for a comprehensive assessment.
        """
        
        st.session_state.messages.append({"role": "assistant", "content": fallback_report})
        return fallback_report

# Streamlit UI
st.title("Mental Health Initial Diagnosis Chatbot")

# Add an auto-scroll container for the chat
chat_container = st.container()

# Show welcome message if no messages exist
if not st.session_state.messages:
    welcome_message = {
        "role": "assistant", 
        "content": """Welcome to the Mental Health Chatbot.

***I'm here to help assess your mental health and provide initial diagnosis. We'll start with a conversation to understand your concerns, then I may ask you to complete one or more standardized assessments, and finally I'll provide a report summarizing our findings.***

***Please note that this is not a substitute for professional medical advice, diagnosis, or treatment. If you're experiencing a mental health emergency, please contact emergency services or a crisis helpline immediately.***

***The conversation is confidential and will not be shared with anyone without your consent.***

Hi, what is your name?"""
    }
    st.session_state.messages.append(welcome_message)

# Display chat messages in the scrollable container
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Auto-scroll to the bottom (using JavaScript)
    if st.session_state.messages:
        js = '''
        <script>
            function scrollToBottom() {
                const messages = document.querySelector('[data-testid="stChatMessageContainer"]');
                if (messages) {
                    messages.scrollTop = messages.scrollHeight;
                }
            }
            scrollToBottom();
        </script>
        '''
        st.components.v1.html(js, height=0)

# Input for user - always show the input box
user_input = st.chat_input("Type your message here...")
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Get response based on current state
    if st.session_state.chat_state == "screening":
        response = screening_agent(user_input)
        # The screening agent handles adding the response to the chat history
    elif st.session_state.chat_state == "assessment":
        # Process the text input even during assessment
        # Let the user know they can continue with the assessment using the buttons
        response = "I see you've sent a message during the assessment. Please use the buttons above to answer the current assessment question. If you need to stop the assessment, you can click 'Start New Conversation'."
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:  # report
        response = "Your diagnosis report has been generated. Is there anything specific you'd like to know?"
        if st.session_state.messages[-1]["role"] != "assistant":
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Force rerun to display new messages in the chat
    st.rerun()

# If in assessment state, display the assessment interface
if st.session_state.chat_state == "assessment" and st.session_state.current_assessment:
    # Call assessment agent to display the current question and handle responses
    assessment_agent()

# If in report state, show generate report button
if st.session_state.chat_state == "report":
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Generate Report"):
            with st.spinner("Generating report..."):
                report = generate_report()
                st.rerun()

# Reset button
if st.button("Start New Conversation"):
    st.session_state.messages = []
    st.session_state.chat_state = "screening"
    st.session_state.diagnosis = {
        "possible_conditions": [],
        "assessment_results": {},
        "final_diagnosis": "",
        "recommendations": ""
    }
    st.session_state.current_assessment = None
    st.session_state.assessment_responses = {}
    st.session_state.assessment_index = 0
    st.rerun()

# Display current state (for debugging)
if st.checkbox("Show Debug Info"):
    st.write(f"Current State: {st.session_state.chat_state}")
    st.write(f"Current Assessment: {st.session_state.current_assessment}")
    st.write(f"Assessment Index: {st.session_state.assessment_index}")
    st.write(f"Diagnosis Data: {st.session_state.diagnosis}")
    st.write(f"Assessment Responses: {st.session_state.assessment_responses}") 

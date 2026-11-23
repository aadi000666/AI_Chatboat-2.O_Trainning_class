import re
from typing import NamedTuple, Optional


class EmotionalAnalysisResult(NamedTuple):
    is_emotional_context: bool
    is_crisis: bool
    detected_emotion: Optional[str]
    crisis_response: Optional[str]
    support_system_instruction: str


class EmotionalSupportService:
    CRISIS_PATTERNS = [
        re.compile(r"\b(suicide|kill\s+myself|end\s+my\s+life|want\s+to\s+die|harm\s+myself|self\s*harm)\b", re.IGNORECASE),
        re.compile(r"\b(don'?t\s+want\s+to\s+live|better\s+off\s+dead|no\s+reason\s+to\s+live)\b", re.IGNORECASE)
    ]

    EMOTION_PATTERNS = {
        "sadness": re.compile(r"\b(sad|depressed|unhappy|crying|hopeless|heartbroken|miserable|grief)\b", re.IGNORECASE),
        "stress": re.compile(r"\b(stressed|anxious|overwhelmed|panic|pressure|burnout|exhausted|nervous)\b", re.IGNORECASE),
        "loneliness": re.compile(r"\b(lonely|alone|isolated|nobody\s+cares|no\s+friends|abandoned)\b", re.IGNORECASE),
        "frustration": re.compile(r"\b(frustrated|angry|furious|mad|irritated|annoyed|resentful)\b", re.IGNORECASE)
    }

    CRISIS_INTERVENTION_MESSAGE = (
        "I hear how much pain you are experiencing right now, and I care about your safety. "
        "I am an AI assistant and not a therapist or crisis counselor, but please know that you do not have to carry this alone.\n\n"
        "If you are in immediate danger or feeling overwhelmed, please connect with people who can support you right away:\n"
        "• **In the US & Canada:** Call or text **988** to reach the Suicide & Crisis Lifeline (free, confidential, 24/7).\n"
        "• **Crisis Text Line:** Text **HOME to 741741**.\n"
        "• **In the UK:** Call **111** or contact Samaritans at **116 123**.\n"
        "• **In India:** Call **9152987821** (AASRA) or **112** for emergency services.\n"
        "• **International:** Find local support at [findahelpline.com](https://findahelpline.com).\n\n"
        "Please reach out to a trusted loved one, family member, doctor, or local emergency services right now."
    )

    EMPATHETIC_SYSTEM_INSTRUCTION = (
        "\n\n--- PERSONAL EMOTIONAL SUPPORT GUIDANCE ---\n"
        "The user is expressing emotional distress or personal difficulty. "
        "Adopt an empathetic, respectful, calm, non-judgmental, and validating tone. "
        "Acknowledge and validate their feelings without offering unsupported medical or psychological diagnoses. "
        "Suggest gentle, healthy coping strategies (such as deep breathing, taking a brief pause, journaling, or speaking to a trusted friend). "
        "Ask a gentle reflective question to help them process their thoughts. "
        "Always remember: You are an AI companion, not a licensed therapist or medical professional. "
        "Never encourage emotional dependency on AI, never claim to replace human connection, and encourage seeking support from qualified professionals or trusted loved ones when needed."
    )

    def analyze_emotional_context(self, user_message: str) -> EmotionalAnalysisResult:
        for pattern in self.CRISIS_PATTERNS:
            if pattern.search(user_message):
                return EmotionalAnalysisResult(
                    is_emotional_context=True,
                    is_crisis=True,
                    detected_emotion="crisis",
                    crisis_response=self.CRISIS_INTERVENTION_MESSAGE,
                    support_system_instruction=""
                )

        detected_emotion = None
        for emotion, pattern in self.EMOTION_PATTERNS.items():
            if pattern.search(user_message):
                detected_emotion = emotion
                break

        is_emotional = detected_emotion is not None

        return EmotionalAnalysisResult(
            is_emotional_context=is_emotional,
            is_crisis=False,
            detected_emotion=detected_emotion,
            crisis_response=None,
            support_system_instruction=self.EMPATHETIC_SYSTEM_INSTRUCTION if is_emotional else ""
        )


emotional_support_service = EmotionalSupportService()

from app.modules.ai_engine.context import AIContext

from app.modules.advisor.prompts import (
    advisor_system_prompt,
    advisor_user_prompt,
)

from app.modules.advisor.schemas import (
    DailyAdvisorResponse,
)

from app.modules.ai_engine.parser import (
    AIResponseParser,
)

from app.modules.ai_engine.orchestrator import (
    AIOrchestrator,
)


class AdvisorPlanner:

    def __init__(self):
        self.orchestrator = AIOrchestrator()

    async def generate_daily_advice(
        self,
        context: AIContext,
    ) -> DailyAdvisorResponse:

        system_prompt = advisor_system_prompt()

        user_prompt = advisor_user_prompt(
            crop_name=context.crop_name,
            crop_variety=context.crop_variety,
            crop_age_days=context.crop_age_days,
            soil_type=context.soil_type,
            location=context.location,
            weather=context.weather,
            temperature=context.temperature,
            humidity=context.humidity,
            rain_probability=context.rain_probability,
            today_activities=context.today_activities,
        )

        response = await self.orchestrator.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=1000,
        )

        return AIResponseParser.parse_daily_advice(
            response,
        )
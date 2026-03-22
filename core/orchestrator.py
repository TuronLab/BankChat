from core.agents.agent_base import AgentBase
from core.data.load_data import BaseDataLoader
from core.inferencer import BaseInferencer
from core.session_manager.models import State
from core.session_manager.session import Session


class Orchestrator:

    def __init__(
            self,
            inferencer_engine: BaseInferencer,
            database_loader: BaseDataLoader,
            greeter_agent: AgentBase,
            bouncer_agent: AgentBase,
            specialist_agent: AgentBase,
    ):
        self.inferencer_engine = inferencer_engine
        self.database_loader = database_loader
        self.greeter_agent = greeter_agent
        self.bouncer_agent = bouncer_agent
        self.specialist_agent = specialist_agent

    def __call__(self, session: Session, message: str) -> str:

        if session.state == State.VERIFYING:
            ## Greeter agent
            greeter_response = self.greeter_agent.step(message=message, session=session)

            if greeter_response.client is None:
                return greeter_response.message
            else:
                session.client = greeter_response.client

            ## Bouncer agent (just looks in the Client object found, with all the data of the database)
            type_client = self.bouncer_agent.step(message=message, session=session)

            session.update_state(State.VERIFIED)

            return greeter_response.message

        elif session.state == State.VERIFIED:
            ## Specialist agent. This agent will try to success in the task described by the user by using the
            ## set of tools described in its initialization
            specialist_response = self.specialist_agent.step(message=message, session=session)
            return specialist_response
        else:
            raise Exception("State not implemented")

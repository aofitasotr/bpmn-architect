from app.agents.state import BPMNState


def generate_process_model(
    state: BPMNState
) -> BPMNState:
    # TODO: LLM -> structured BPMN model

    model = {
        "nodes":[
            {
                "id":"start",
                "type":"startEvent",
                "name":"Начало"
            },
            {
                "id":"task1",
                "type":"userTask",
                "name":"Создать заявку"
            },
            {
                "id":"end",
                "type":"endEvent",
                "name":"Конец"
            }
        ],

        "flows":[
            {
                "from":"start",
                "to":"task1"
            },
            {
                "from":"task1",
                "to":"end"
            }
        ]
    }


    return {
        **state,
        "process_model": model
    }
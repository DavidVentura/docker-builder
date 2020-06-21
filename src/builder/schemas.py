WEBHOOK_SCHEMA = {
	"$schema": "http://json-schema.org/draft-04/schema#",
	"type": "object",
	"properties": {
	    "ref": {"type": "string"},
	    "ref_type": {"type": "string", "enum": ["branch", "tag"] },
	    "commits": {
		"type": "array",
		"items": [
		    {
			"type": "object",
			"properties": {
			    "id": {"type": "string"},
			    "message": {"type": "string"},
			    "timestamp": {"type": "string"}
			    },
			"required": ["id", "message", "timestamp"]
			}
		    ]
		},
	    "repository": {
		"type": "object",
		"properties": {
		    "ssh_url": {"type": "string"}
		    },
		"required": ["ssh_url"]
		}
	    },
	"required": ["ref", "repository"],
        "anyOf": [
            {
                "required": ["ref_type"],
                },
            {
                "required": ["commits"],
                },
            ],
        }

variable "aws_region" {
  description = "Deployment region (e.g.: ca-central-1)."
  type        = string
  default     = "ca-central-1"
}

variable "bucket_name" {
  description = "Name for S3 bucket and lambda function"
  type        = string
  default     = "quetzal-api-bucket"
}

locals {
  general_tags = {
    "cost:project" : "quetzal",
    "cost:name" : "${var.bucket_name}"
  }
  gtfs_api_tags = {
    "cost:project" : "quetzal",
    "cost:name" : "${var.gtfs_api_name}"
  }
   osm_api_tags = {
    "cost:project" : "quetzal",
    "cost:name" : "${var.osm_api_name}"
  }
  matrixroadcaster_api_tags = {
    "cost:project" : "quetzal",
    "cost:name" : "${var.matrixroadcaster_api_name}"
  }
}

# =========
# GTFS API
# =========

variable "gtfs_api_name" {
  description = "Name of the GTFS importer api"
  type        = string
  default     = "quetzal-gtfs-api"
}

variable "gtfs_api_memory_size" {
  description = "Lambda function ram in mb"
  default     = 5120
  type        = number
}

variable "gtfs_api_time_limit" {
  description = "Lambda function time limit in seconds"
  default     = 600
  type        = number
}

variable "gtfs_api_storage_size" {
  description = "Lambda function ephemeral storage size in mb"
  default     = 512
  type        = number
}

variable "gtfs_api_state_machine" {
  description = "New state machine definition"
  type        = string
  default     = <<EOF
    {
      "Comment": "step function calling the lambda function",
      "StartAt": "api call",
      "States": {
        "api call": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "OutputPath": "$.Payload",
          "Parameters": {
            "Payload.$": "$",
            "FunctionName": "arn:aws:lambda:ca-central-1:142023388927:function:quetzal-gtfs-api:$LATEST"
          },
          "Retry": [
            {
              "ErrorEquals": [
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
                "Lambda.TooManyRequestsException"
              ],
              "IntervalSeconds": 2,
              "MaxAttempts": 6,
              "BackoffRate": 2
            }
          ],
          "End": true
        }
      }
    }
    EOF
}

# =========
# OSM API
# =========

variable "osm_api_name" {
  description = "Name of the GTFS importer api"
  type        = string
  default     = "quetzal-osm-api"
}

variable "osm_api_memory_size" {
  description = "Lambda function ram in mb"
  default     = 10240
  type        = number
}

variable "osm_api_time_limit" {
  description = "Lambda function time limit in seconds"
  default     = 600
  type        = number
}

variable "osm_api_storage_size" {
  description = "Lambda function ephemeral storage size in mb"
  default     = 512
  type        = number
}

variable "osm_api_state_machine" {
  description = "New state machine definition"
  type        = string
  default     = <<EOF
    {
      "Comment": "step function calling the lambda function",
      "StartAt": "api call",
      "States": {
        "api call": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "OutputPath": "$.Payload",
          "Parameters": {
            "Payload.$": "$",
            "FunctionName": "arn:aws:lambda:ca-central-1:142023388927:function:quetzal-osm-api:$LATEST"
          },
          "Retry": [
            {
              "ErrorEquals": [
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
                "Lambda.TooManyRequestsException"
              ],
              "IntervalSeconds": 2,
              "MaxAttempts": 6,
              "BackoffRate": 2
            }
          ],
          "End": true
        }
      }
    }
    EOF
}

# =========
# matrixroadcaster API
# =========

variable "matrixroadcaster_api_name" {
  description = "Name of the GTFS importer api"
  type        = string
  default     = "quetzal-matrixroadcaster-api"
}

variable "matrixroadcaster_api_memory_size" {
  description = "Lambda function ram in mb"
  default     = 5120
  type        = number
}

variable "matrixroadcaster_api_time_limit" {
  description = "Lambda function time limit in seconds"
  default     = 900
  type        = number
}

variable "matrixroadcaster_api_storage_size" {
  description = "Lambda function ephemeral storage size in mb"
  default     = 512
  type        = number
}

variable "matrixroadcaster_api_state_machine" {
  description = "New state machine definition"
  type        = string
  default     = <<EOF
    {
      "Comment": "step function calling the lambda function",
      "StartAt": "api call",
      "States": {
        "api call": {
          "Type": "Task",
          "Resource": "arn:aws:states:::lambda:invoke",
          "OutputPath": "$.Payload",
          "Parameters": {
            "Payload.$": "$",
            "FunctionName": "arn:aws:lambda:ca-central-1:142023388927:function:quetzal-matrixroadcaster-api:$LATEST"
          },
          "Retry": [
            {
              "ErrorEquals": [
                "Lambda.ServiceException",
                "Lambda.AWSLambdaException",
                "Lambda.SdkClientException",
                "Lambda.TooManyRequestsException"
              ],
              "IntervalSeconds": 2,
              "MaxAttempts": 6,
              "BackoffRate": 2
            }
          ],
          "End": true
        }
      }
    }
    EOF
}
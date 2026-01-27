import { useProviderFields } from "@/app/(dashboard)/hooks/providers/useProviderFields";
import { UploadOutlined } from "@ant-design/icons";
import { Text, TextInput } from "@tremor/react";
import { Button as Button2, Col, Form, Input, Row, Select, Typography, Upload, UploadProps } from "antd";
import React from "react";
import { CredentialItem, ProviderCredentialFieldMetadata } from "../networking";
import { provider_map, Providers } from "../provider_info_helpers";
const { Link } = Typography;

interface ProviderSpecificFieldsProps {
  selectedProvider: Providers;
  uploadProps?: UploadProps;
}

interface ProviderCredentialField {
  key: string;
  label: string;
  placeholder?: string;
  tooltip?: string;
  required?: boolean;
  type?: "text" | "password" | "select" | "upload" | "textarea";
  options?: string[];
  defaultValue?: string;
}

export interface CredentialValues {
  key: string;
  value: string;
}

const mapFieldMetadataToUiField = (field: ProviderCredentialFieldMetadata): ProviderCredentialField => {
  const type: ProviderCredentialField["type"] =
    field.field_type === "password"
      ? "password"
      : field.field_type === "select"
        ? "select"
        : field.field_type === "upload"
          ? "upload"
          : field.field_type === "textarea"
            ? "textarea"
            : "text";

  return {
    key: field.key,
    label: field.label,
    placeholder: field.placeholder ?? undefined,
    tooltip: field.tooltip ?? undefined,
    required: field.required ?? false,
    type,
    options: field.options ?? undefined,
    defaultValue: field.default_value ?? undefined,
  };
};

// In-memory cache of provider credential fields keyed by provider display name.
// This lets us reuse the data across multiple mounts and also supports
// non-React helpers like createCredentialFromModel.
const providerFieldsByDisplayName: Record<string, ProviderCredentialField[]> = {};

export const createCredentialFromModel = (provider: string, modelData: any): CredentialItem => {
  console.log("provider", provider);
  console.log("modelData", modelData);
  const enumKey = Object.keys(provider_map).find((key) => provider_map[key].toLowerCase() === provider.toLowerCase());
  if (!enumKey) {
    throw new Error(`Provider ${provider} not found in provider_map`);
  }
  const providerDisplayName = Providers[enumKey as keyof typeof Providers];
  const providerFields = providerFieldsByDisplayName[providerDisplayName] || [];
  const credentialValues: object = {};

  console.log("providerFields", providerFields);

  // Go through each field defined for this provider
  providerFields.forEach((field) => {
    const value = modelData.litellm_params[field.key];
    console.log("field", field);
    console.log("value", value);
    if (value !== undefined) {
      (credentialValues as Record<string, string>)[field.key] = value.toString();
    }
  });

  const credential: CredentialItem = {
    credential_name: `${provider}-credential-${Math.floor(Math.random() * 1000000)}`,
    credential_values: credentialValues,
    credential_info: {
      custom_llm_provider: provider,
      description: `Credential for ${provider}. Created from model ${modelData.model_name}`,
    },
  };

  return credential;
};

const PROVIDER_CREDENTIAL_FIELDS: Record<Providers, ProviderCredentialField[]> = {
  [Providers.OpenAI]: [
    {
      key: "api_base",
      label: "API Base",
      type: "select",
      options: ["https://api.openai.com/v1", "https://eu.api.openai.com"],
      defaultValue: "https://api.openai.com/v1",
    },
    {
      key: "organization",
      label: "OpenAI Organization ID",
      placeholder: "[OPTIONAL] my-unique-org",
    },
    {
      key: "api_key",
      label: "OpenAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.OpenAI_Text]: [
    {
      key: "api_base",
      label: "API Base",
      type: "select",
      options: ["https://api.openai.com/v1", "https://eu.api.openai.com"],
      defaultValue: "https://api.openai.com/v1",
    },
    {
      key: "organization",
      label: "OpenAI Organization ID",
      placeholder: "[OPTIONAL] my-unique-org",
    },
    {
      key: "api_key",
      label: "OpenAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Vertex_AI]: [
    {
      key: "vertex_project",
      label: "Vertex Project",
      placeholder: "adroit-cadet-1234..",
      required: true,
    },
    {
      key: "vertex_location",
      label: "Vertex Location",
      placeholder: "us-east-1",
      required: true,
    },
    {
      key: "vertex_credentials",
      label: "Vertex Credentials",
      required: true,
      type: "upload",
    },
  ],
  [Providers.AssemblyAI]: [
    {
      key: "api_base",
      label: "API Base",
      type: "select",
      required: true,
      options: ["https://api.assemblyai.com", "https://api.eu.assemblyai.com"],
    },
    {
      key: "api_key",
      label: "AssemblyAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Azure]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "https://...",
      required: true,
    },
    {
      key: "api_version",
      label: "API Version",
      placeholder: "2023-07-01-preview",
      tooltip:
        "By default litellm will use the latest version. If you want to use a different version, you can specify it here",
    },
    {
      key: "base_model",
      label: "Base Model",
      placeholder: "azure/gpt-3.5-turbo",
    },
    {
      key: "api_key",
      label: "Azure API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Azure_AI_Studio]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "https://<test>.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21",
      tooltip:
        "Enter your full Target URI from Azure Foundry here. Example:  https://litellm8397336933.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-10-21",
      required: true,
    },
    {
      key: "api_key",
      label: "Azure API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.OpenAI_Compatible]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "https://...",
      required: true,
    },
    {
      key: "api_key",
      label: "OpenAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Dashscope]: [
    {
      key: "api_key",
      label: "Dashscope API Key",
      type: "password",
      required: true,
    },
    {
      key: "api_base",
      label: "API Base",
      placeholder: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
      defaultValue: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
      required: true,
      tooltip:
        "The base URL for your Dashscope server. Defaults to https://dashscope-intl.aliyuncs.com/compatible-mode/v1 if not specified.",
    },
  ],
  [Providers.OpenAI_Text_Compatible]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "https://...",
      required: true,
    },
    {
      key: "api_key",
      label: "OpenAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Bedrock]: [
    {
      key: "aws_access_key_id",
      label: "AWS Access Key ID",
      type: "password",
      required: false,
      tooltip: "You can provide the raw key or the environment variable (e.g. `os.environ/MY_SECRET_KEY`).",
    },
    {
      key: "aws_secret_access_key",
      label: "AWS Secret Access Key",
      type: "password",
      required: false,
      tooltip: "You can provide the raw key or the environment variable (e.g. `os.environ/MY_SECRET_KEY`).",
    },
    {
      key: "aws_session_token",
      label: "AWS Session Token",
      type: "password",
      required: false,
      tooltip:
        "Temporary credentials session token. You can provide the raw token or the environment variable (e.g. `os.environ/MY_SESSION_TOKEN`).",
    },
    {
      key: "aws_region_name",
      label: "AWS Region Name",
      placeholder: "us-east-1",
      required: false,
      tooltip: "You can provide the raw key or the environment variable (e.g. `os.environ/MY_SECRET_KEY`).",
    },
    {
      key: "aws_session_name",
      label: "AWS Session Name",
      placeholder: "my-session",
      required: false,
      tooltip:
        "Name for the AWS session. You can provide the raw value or the environment variable (e.g. `os.environ/MY_SESSION_NAME`).",
    },
    {
      key: "aws_profile_name",
      label: "AWS Profile Name",
      placeholder: "default",
      required: false,
      tooltip:
        "AWS profile name to use for authentication. You can provide the raw value or the environment variable (e.g. `os.environ/MY_PROFILE_NAME`).",
    },
    {
      key: "aws_role_name",
      label: "AWS Role Name",
      placeholder: "MyRole",
      required: false,
      tooltip:
        "AWS IAM role name to assume. You can provide the raw value or the environment variable (e.g. `os.environ/MY_ROLE_NAME`).",
    },
    {
      key: "aws_web_identity_token",
      label: "AWS Web Identity Token",
      type: "password",
      required: false,
      tooltip:
        "Web identity token for OIDC authentication. You can provide the raw token or the environment variable (e.g. `os.environ/MY_WEB_IDENTITY_TOKEN`).",
    },
    {
      key: "aws_bedrock_runtime_endpoint",
      label: "AWS Bedrock Runtime Endpoint",
      placeholder: "https://bedrock-runtime.us-east-1.amazonaws.com",
      required: false,
      tooltip:
        "Custom Bedrock runtime endpoint URL. You can provide the raw value or the environment variable (e.g. `os.environ/MY_BEDROCK_ENDPOINT`).",
    },
  ],
  [Providers.SageMaker]: [
    {
      key: "aws_access_key_id",
      label: "AWS Access Key ID",
      type: "password",
      required: false,
      tooltip: "You can provide the raw key or the environment variable (e.g. `os.environ/MY_SECRET_KEY`).",
    },
    {
      key: "aws_secret_access_key",
      label: "AWS Secret Access Key",
      type: "password",
      required: false,
      tooltip: "You can provide the raw key or the environment variable (e.g. `os.environ/MY_SECRET_KEY`).",
    },
    {
      key: "aws_region_name",
      label: "AWS Region Name",
      placeholder: "us-east-1",
      required: false,
      tooltip: "You can provide the raw key or the environment variable (e.g. `os.environ/MY_SECRET_KEY`).",
    },
  ],
  [Providers.Ollama]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "http://localhost:11434",
      defaultValue: "http://localhost:11434",
      required: false,
      tooltip: "The base URL for your Ollama server. Defaults to http://localhost:11434 if not specified.",
    },
  ],
  [Providers.Anthropic]: [
    {
      key: "api_key",
      label: "API Key",
      placeholder: "sk-",
      type: "password",
      required: true,
    },
  ],
  [Providers.Deepgram]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.ElevenLabs]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Google_AI_Studio]: [
    {
      key: "api_key",
      label: "API Key",
      placeholder: "aig-",
      type: "password",
      required: true,
    },
  ],
  [Providers.Groq]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.MistralAI]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Deepseek]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Cohere]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Databricks]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.xAI]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.AIML]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Cerebras]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Sambanova]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Perplexity]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.TogetherAI]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Openrouter]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.FireworksAI]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.GradientAI]: [
    {
      key: "api_base",
      label: "GradientAI Endpoint",
      placeholder: "https://...",
      required: false,
    },
    {
      key: "api_key",
      label: "GradientAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Triton]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: false,
    },
    {
      key: "api_base",
      label: "API Base",
      placeholder: "http://localhost:8000/generate",
      required: false,
    },
  ],
  [Providers.Hosted_Vllm]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "https://...",
      required: true,
    },
    {
      key: "api_key",
      label: "OpenAI API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Voyage]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.JinaAI]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.VolcEngine]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.DeepInfra]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Oracle]: [
    {
      key: "api_key",
      label: "API Key",
      type: "password",
      required: true,
    },
  ],
  [Providers.Snowflake]: [
    {
      key: "api_key",
      label: "Snowflake API Key / JWT Key for Authentication",
      type: "password",
      required: true,
    },
    {
      key: "api_base",
      label: "Snowflake API Endpoint",
      placeholder: "https://1234567890.snowflakecomputing.com/api/v2/cortex/inference:complete",
      tooltip:
        "Enter the full endpoint with path here. Example: https://1234567890.snowflakecomputing.com/api/v2/cortex/inference:complete",
      required: true,
    },
  ],
  [Providers.Infinity]: [
    {
      key: "api_base",
      label: "API Base",
      placeholder: "http://localhost:7997",
    },
  ],
};

const ProviderSpecificFields: React.FC<ProviderSpecificFieldsProps> = ({ selectedProvider, uploadProps }) => {
  const selectedProviderEnum = Providers[selectedProvider as keyof typeof Providers] as Providers;
  const form = Form.useFormInstance(); // Get form instance from context

  const { data: providerMetadata, isLoading, error: loadError } = useProviderFields();

  // Memoize the expensive cache computation
  const cacheEntries = React.useMemo(() => {
    if (!providerMetadata) {
      return null;
    }

    // Compute cache entries keyed by provider display name and identifiers
    const entries: Record<string, ProviderCredentialField[]> = {};
    providerMetadata.forEach((providerInfo) => {
      const displayName = providerInfo.provider_display_name;
      const mappedFields = providerInfo.credential_fields.map(mapFieldMetadataToUiField);

      // Primary key: human-readable display name
      entries[displayName] = mappedFields;

      // Also cache by backend identifiers so lookups by provider slug work
      if (providerInfo.provider) {
        entries[providerInfo.provider] = mappedFields;
      }
      if (providerInfo.litellm_provider) {
        entries[providerInfo.litellm_provider] = mappedFields;
      }
    });
    return entries;
  }, [providerMetadata]);

  // Sync memoized cache entries to module-level cache
  React.useEffect(() => {
    if (!cacheEntries) {
      return;
    }

    Object.assign(providerFieldsByDisplayName, cacheEntries);
  }, [cacheEntries]);

  const allFields = React.useMemo(() => {
    // First try to resolve from the in-memory cache. We support both the
    // enum/display-name form and the raw provider slug (e.g. "petals").
    const cachedFields =
      providerFieldsByDisplayName[selectedProviderEnum] ?? providerFieldsByDisplayName[selectedProvider];
    if (cachedFields) {
      return cachedFields;
    }

    if (!providerMetadata) {
      return [];
    }

    const providerInfo = providerMetadata.find(
      (p) =>
        p.provider_display_name === selectedProviderEnum ||
        p.provider === selectedProvider ||
        p.litellm_provider === selectedProvider,
    );
    if (!providerInfo) {
      return [];
    }

    const mapped = providerInfo.credential_fields.map(mapFieldMetadataToUiField);
    providerFieldsByDisplayName[providerInfo.provider_display_name] = mapped;
    if (providerInfo.provider) {
      providerFieldsByDisplayName[providerInfo.provider] = mapped;
    }
    if (providerInfo.litellm_provider) {
      providerFieldsByDisplayName[providerInfo.litellm_provider] = mapped;
    }
    return mapped;
  }, [selectedProviderEnum, selectedProvider, providerMetadata]);

  const handleUpload = {
    name: "file",
    accept: ".json",
    beforeUpload: (file: any) => {
      if (file.type === "application/json") {
        const reader = new FileReader();
        reader.onload = (e) => {
          if (e.target) {
            const jsonStr = e.target.result as string;
            console.log(`Setting field value from JSON, length: ${jsonStr.length}`);
            form.setFieldsValue({ vertex_credentials: jsonStr });
            console.log("Form values after setting:", form.getFieldsValue());
          }
        };
        reader.readAsText(file);
      }
      // Prevent upload
      return false;
    },
    onChange(info: any) {
      console.log("Upload onChange triggered in ProviderSpecificFields");
      console.log("Current form values:", form.getFieldsValue());

      if (info.file.status !== "uploading") {
        console.log(info.file, info.fileList);
      }
    },
  };

  return (
    <>
      {isLoading && allFields.length === 0 && (
        <Row>
          <Col span={24}>
            <Text className="mb-2">Loading provider fields...</Text>
          </Col>
        </Row>
      )}
      {loadError && allFields.length === 0 && (
        <Row>
          <Col span={24}>
            <Text className="mb-2 text-red-500">
              {loadError instanceof Error ? loadError.message : "Failed to load provider credential fields"}
            </Text>
          </Col>
        </Row>
      )}
      {allFields.map((field) => (
        <React.Fragment key={field.key}>
          <Form.Item
            label={field.label}
            name={field.key}
            rules={field.required ? [{ required: true, message: "Required" }] : undefined}
            tooltip={field.tooltip}
            className={field.key === "vertex_credentials" ? "mb-0" : undefined}
          >
            {field.type === "select" ? (
              <Select placeholder={field.placeholder} defaultValue={field.defaultValue}>
                {field.options?.map((option) => (
                  <Select.Option key={option} value={option}>
                    {option}
                  </Select.Option>
                ))}
              </Select>
            ) : field.type === "upload" ? (
              <Upload
                {...handleUpload}
                onChange={(info) => {
                  // First call the original onChange
                  if (uploadProps?.onChange) {
                    uploadProps.onChange(info);
                  }

                  // Check the field value after a short delay
                  setTimeout(() => {
                    const value = form.getFieldValue(field.key);
                    console.log(`${field.key} value after upload:`, JSON.stringify(value));
                  }, 500);
                }}
              >
                <Button2 icon={<UploadOutlined />}>Click to Upload</Button2>
              </Upload>
            ) : field.type === "textarea" ? (
              <Input.TextArea
                placeholder={field.placeholder}
                defaultValue={field.defaultValue}
                rows={6}
                style={{ fontFamily: "monospace", fontSize: "12px" }}
              />
            ) : (
              <TextInput
                placeholder={field.placeholder}
                type={field.type === "password" ? "password" : "text"}
                defaultValue={field.defaultValue}
              />
            )}
          </Form.Item>

          {/* Special case for Vertex Credentials help text */}
          {field.key === "vertex_credentials" && (
            <Row>
              <Col>
                <Text className="mb-3 mt-1">Give a gcp service account(.json file)</Text>
              </Col>
            </Row>
          )}

          {/* Special case for Azure Base Model help text */}
          {field.key === "base_model" && (
            <Row>
              <Col span={10}></Col>
              <Col span={10}>
                <Text className="mb-2">
                  The actual model your azure deployment uses. Used for accurate cost tracking. Select name from{" "}
                  <Link
                    href="https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json"
                    target="_blank"
                  >
                    here
                  </Link>
                </Text>
              </Col>
            </Row>
          )}
        </React.Fragment>
      ))}
    </>
  );
};

export default ProviderSpecificFields;

module github.com/opendatalab/MinerU-Ecosystem/cli

go 1.21

require (
	github.com/opendatalab/MinerU-Ecosystem/sdk/go v0.0.0
	github.com/spf13/cobra v1.8.0
	gopkg.in/yaml.v3 v3.0.1
)

replace github.com/opendatalab/MinerU-Ecosystem/sdk/go => ../mineru-open-sdk-go

require (
	github.com/inconshreveable/mousetrap v1.1.0 // indirect
	github.com/spf13/pflag v1.0.5 // indirect
)

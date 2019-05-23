# Item Checkout Feed

## Backend: ItemCheckoutFeedUpdater

Repo: https://github.com/NYPL/item-checkout-feed-updater

### S3

The updater [writes to the configured S3 Bucket](https://github.com/NYPL/item-checkout-feed-updater/blob/8085b09540b45442fb8ffc2ae520f165e307114e/lib/s3_writer.rb#L84). At writing, these buckets are:

 * `item-checkout-feed-production`: Production feed (and viewer)
 * `item-checkout-feed-qa`: Production feed (and viewer)
 * `item-checkout-feed-test`: A "dev" bucket useful for local testing.

QA and production buckets are configured to be writable by the Updater lambda, but only readable by certain IP blocks. This is managed by:

1. Enable public access via:
  * S3 > item-checkout-feed-[env] > Permissions > Block public access
  * Disable all blocks so that "Block *all* public access" is "Off". (Note: It's not clear why blocking ACLs would prevent a bucket policy from taking effect, but that does seem to be the case.)
1. Enable restricted reads/writes by bucket policy:
  * S3 > item-checkout-feed-[env] > Permissions > Bucket Policy
  * Enter the following (replace "-qa" with relevant suffix):
  
```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Deny",
            "Principal": {
                "AWS": "*"
            },
            "Action": "s3:GetObject",
            "Resource": [
                "arn:aws:s3:::item-checkout-feed-qa2",
                "arn:aws:s3:::item-checkout-feed-qa2/*"
            ],
            "Condition": {
                "NotIpAddress": {
                    "aws:SourceIp": [
                        "65.88.88.0/24",
                        "65.88.89.35/32",
                        "65.88.89.45/32",
                        "10.128.64.0/24",
                        "10.128.65.0/24",
                        "10.128.66.0/24",
                        "10.128.67.0/24",
                        "10.144.64.0/24",
                        "10.160.64.0/24",
                        "10.176.64.0/24",
                        "10.224.118.53/32",
                        "172.16.1.43/32"
                    ]
                }
            }
        },
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::946183545209:role/lambda-full-access"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject"
            ],
            "Resource": [
                "arn:aws:s3:::item-checkout-feed-qa2",
                "arn:aws:s3:::item-checkout-feed-qa2/*"
            ]
        }
    ]
}
```

Above CIDRs approximate the IPs of traffic originating from NYPL branches, borrowed from [Digital Collections](https://github.com/NYPL/digitalreadingroom/blob/1b1c6610d6174294d28c450fcaee434c7c90a0a9/lib/rights_methods.rb#L69-L193). The only known issue is it matches all of `65.88.88.0/24` rather matching each of the actual 167 allowed IPs under `65.88.88.` - leading to possibly broader access than strictly appropriate.

## Frontend: ItemFeedViewer

Repo: https://github.com/NYPL/item-feed-viewer

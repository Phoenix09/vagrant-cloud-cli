#!/usr/bin/python3
import argparse
import sys

from vagrant_cloud_cli.vcapi import VagrantCloudApi


class MyArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        exit(2)


def main():
    parser = MyArgumentParser(description="API token must be set in either the 'ATLAS_TOKEN' or "
                                          "'VAGRANT_CLOUD_TOKEN' environment variable")
    VC = VagrantCloudApi(parser)
    subparsers = parser.add_subparsers(title="Commands", dest="command")
    subparsers.required = True

    # Authenticate
    parser_validate = subparsers.add_parser("authenticate", help="Get an API token")
    parser_validate.set_defaults(func=VC.authenticate)

    # Validate
    parser_validate = subparsers.add_parser("validate", help="Validate API token")
    parser_validate.set_defaults(func=VC.validate)

    parser_user = subparsers.add_parser("user", help="Get information about a user")
    parser_user.add_argument("username")
    parser_user.set_defaults(func=VC.user)

    # Box Management
    parser_box = subparsers.add_parser("box", help="Box actions")

    # Actions for Boxes
    subparsers_box = parser_box.add_subparsers(title="Actions", dest="action")
    subparsers_box.required = True

    # Box Info
    parser_box_info = subparsers_box.add_parser("info", help="Get information about a box")
    parser_box_info.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_info.set_defaults(func=VC.box_info)

    # Box Create
    parser_box_create = subparsers_box.add_parser("create", help="Create a box")
    parser_box_create.add_argument("username", help="The username of the organization that will own this box")
    parser_box_create.add_argument("box", help="The name of the box")
    parser_box_create.add_argument("-d", "--description", type=str, help="A short summary of the box")
    parser_box_create.add_argument("-p", "--private", default=False, action="store_true",
                                   help="Whether or not this box is private (default is public)")
    parser_box_create.set_defaults(func=VC.box_create)

    # Box Update
    parser_box_update = subparsers_box.add_parser("update", help="Update a box")
    parser_box_update.add_argument("tag", help="Box tag for the box to update in the format 'myuser/test'")
    parser_box_update.add_argument("-n", "--name", type=str, help="The name of the box")
    parser_box_update.add_argument("-d", "--description", type=str, help="A short summary of the box")
    parser_box_update.add_argument("-p", "--private", default=None, action="store_true",
                                   help="Whether or not this box is private")
    parser_box_update.add_argument("-u", "--public", default=None, action="store_true",
                                   help="Whether or not this box is public")
    parser_box_update.set_defaults(func=VC.box_update)

    # Box Delete
    parser_box_delete = subparsers_box.add_parser("delete", help="Delete a box")
    parser_box_delete.add_argument("tag", help="Box tag for the box to delete in the format 'myuser/test'")
    parser_box_delete.add_argument("-f", "--force", action="store_true", help="Don't prompt for confirmation")
    parser_box_delete.set_defaults(func=VC.box_delete)

    # Box Version Actions
    parser_box_version = subparsers_box.add_parser("version", help="Get version information about a box")
    subparsers_box_version = parser_box_version.add_subparsers(title="Actions", dest="action")
    subparsers_box_version.required = True

    # Box Version Info
    parser_box_version_info = subparsers_box_version.add_parser("info", help="Get version information for a box")
    parser_box_version_info.add_argument("tag", help="Box tag for the box in the format 'myuser/test'")
    parser_box_version_info.add_argument("version", help="Box version")
    parser_box_version_info.set_defaults(func=VC.box_version_info)

    # Box Version Create
    parser_box_version_create = subparsers_box_version.add_parser("create", help="Create a new version for a box")
    parser_box_version_create.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_version_create.add_argument("version", help="Box version to create")
    parser_box_version_create.add_argument("-d", "--description", type=str,
                                           help="A description for this version. Can be formatted with Markdown")
    parser_box_version_create.set_defaults(func=VC.box_version_create)

    # Box Version Update
    parser_box_version_update = subparsers_box_version.add_parser("update", help="Update an existing version of a box")
    parser_box_version_update.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_version_update.add_argument("version", help="Box version to update")
    parser_box_version_update.add_argument("-v", "--version", type=str, metavar="newversion", dest="newversion",
                                           help="The version number of this version")
    parser_box_version_update.add_argument("-d", "--description", type=str,
                                           help="A description for this version. Can be formatted with Markdown")
    parser_box_version_update.set_defaults(func=VC.box_version_update)

    # Box Version Delete
    parser_box_version_delete = subparsers_box_version.add_parser("delete", help="Delete a version of a box")
    parser_box_version_delete.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_version_delete.add_argument("version", help="Version to delete")
    parser_box_version_delete.add_argument("-f", "--force", action="store_true", help="Don't prompt for confirmation")
    parser_box_version_delete.set_defaults(func=VC.box_version_delete)

    # Box Version Release
    parser_box_version_release = subparsers_box_version.add_parser("release", help="Release a version of a box")
    parser_box_version_release.add_argument("tag", help="Box tag for the box in the format 'myuser/test'")
    parser_box_version_release.add_argument("version", help="Box version to release")
    parser_box_version_release.set_defaults(func=VC.box_version_release)

    # Box Version Revoke
    parser_box_version_revoke = subparsers_box_version.add_parser("revoke", help="Revoke a version of a box")
    parser_box_version_revoke.add_argument("tag", help="Box tag for the box in the format 'myuser/test'")
    parser_box_version_revoke.add_argument("version", help="Box version to revoke")
    parser_box_version_revoke.set_defaults(func=VC.box_version_revoke)

    # Box Provider Actions
    parser_box_provider = subparsers_box.add_parser("provider", help="Get provider information about a box")
    subparsers_box_provider = parser_box_provider.add_subparsers(title="Actions", dest="action")
    subparsers_box_provider.required = True

    # Box Provider Info
    parser_box_provider_info = subparsers_box_provider.add_parser("info", help="Get provider information for a box")
    parser_box_provider_info.add_argument("tag", help="Box tag for the box in the format 'myuser/test'")
    parser_box_provider_info.add_argument("version", help="Box version")
    parser_box_provider_info.add_argument("provider", help="Provider to get information about")
    parser_box_provider_info.set_defaults(func=VC.box_provider_info)

    # Box Provider Create
    parser_box_provider_create = subparsers_box_provider.add_parser("create", help="Create a new provider for a box")
    parser_box_provider_create.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_provider_create.add_argument("version", help="Box version")
    parser_box_provider_create.add_argument("provider", help="The name of the provider")
    parser_box_provider_create.add_argument("-u", "--url", type=str,
                                            help="A valid URL to download this provider. If omitted, you must upload the Vagrant box image for this provider to Vagrant Cloud before the provider can be used")
    parser_box_provider_create.set_defaults(func=VC.box_provider_create)

    # Box Provider Update
    parser_box_provider_update = subparsers_box_provider.add_parser("update", help="Update an existing version of a box")
    parser_box_provider_update.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_provider_update.add_argument("version", help="Box version")
    parser_box_provider_update.add_argument("provider", help="Box provider to update")
    parser_box_provider_update.add_argument("-p", "--provider", type=str, metavar="newprovider", dest="newprovider",
                                            help="The name of the provider")
    parser_box_provider_update.add_argument("-u", "--url", type=str,
                                            help="A valid URL to download this provider. If omitted, you must upload the Vagrant box image for this provider to Vagrant Cloud before the provider can be used")
    parser_box_provider_update.set_defaults(func=VC.box_provider_update)

    # Box Provider Delete
    parser_box_provider_delete = subparsers_box_provider.add_parser("delete", help="Delete a version of a box")
    parser_box_provider_delete.add_argument("tag", help="Box tag in the format 'myuser/test'")
    parser_box_provider_delete.add_argument("version", help="Box version")
    parser_box_provider_delete.add_argument("provider", help="Provider to delete")
    parser_box_provider_delete.add_argument("-f", "--force", action="store_true", help="Don't prompt for confirmation")
    parser_box_provider_delete.set_defaults(func=VC.box_provider_delete)

    # Box Provider Upload
    parser_box_provider_upload = subparsers_box_provider.add_parser("upload", help="Upload a box for a provider")
    parser_box_provider_upload.add_argument("tag", help="Box tag for the box in the format 'myuser/test'")
    parser_box_provider_upload.add_argument("version", help="Box version")
    parser_box_provider_upload.add_argument("provider", help="Box provider to upload")
    parser_box_provider_upload.add_argument("file", help="Path to the box to upload")
    parser_box_provider_upload.set_defaults(func=VC.box_provider_upload)

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()

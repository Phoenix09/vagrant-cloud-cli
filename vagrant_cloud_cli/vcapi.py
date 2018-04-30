import os
import sys

from getpass import getpass
import dateutil.parser
import prettytable
import requests


class VagrantCloudApi:
    def __init__(self, parser):
        self.parser = parser
        self.API_ENDPOINT = "https://app.vagrantup.com/api/v1"

        atlas_token = os.environ.get("ATLAS_TOKEN")
        if not atlas_token:
            atlas_token = os.environ.get("VAGRANT_CLOUD_TOKEN")

        if not atlas_token:
            print("Error: Neither ATLAS_TOKEN or VAGRANT_CLOUD_TOKEN are defined", file=sys.stderr)
            exit(1)

        self.s = requests.session()
        self.s.headers.update({
            "Authorization": "Bearer %s" % atlas_token
        })

    def _format_dt(self, date_string):
        dt = dateutil.parser.parse(date_string)
        return dt.strftime("%c")

    def _get(self, page):
        r = self.s.get(self.API_ENDPOINT + page)
        r.raise_for_status()
        return r

    def _post(self, page, data):
        r = self.s.post(self.API_ENDPOINT + page, json=data)
        r.raise_for_status()
        return r

    def _put(self, page, data={}):
        r = self.s.put(self.API_ENDPOINT + page, json=data)
        r.raise_for_status()
        return r

    def _delete(self, page):
        r = self.s.delete(self.API_ENDPOINT + page)
        r.raise_for_status()
        return r

    def _upload(self, upload_path, file):
        with open(file, "rb") as f:
            r = self.s.put(upload_path, data=f)
        r.raise_for_status()
        return r

    def authenticate(self, args):
        raise NotImplementedError("Currently there is no way to know whether 2FA is enabled for an account "
                                  "so this is not implemented right now")
        username = input("Username: ")
        password = getpass()
        data = {
            "token": {
                "description": "vagrant-cloud-cli"
            },
            "user": {
                "login": username,
                "password": password
            }
        }

        r = self._post("/authenticate", data=data)
        print(r.json())

    def validate(self, args):
        try:
            r = self._get("/authenticate")
            print("API Token Validated")
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                print("API Token Invalid")
                return 1
            else:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                raise

    def user(self, args):
        try:
            r = self._get("/user/" + args.username)
            data = r.json()
            if len(data["boxes"]) > 0:
                print("Available boxes for '%s':" % data["username"])
                table = prettytable.PrettyTable(["Name", "Description", "Created", "Updated", "Current Version"])
                for box in data["boxes"]:
                    box["current_version"] = box["current_version"]["version"] if box[
                        "current_version"] else "None Released"
                    table.add_row(
                        [box["name"], box["short_description"], self._format_dt(box["created_at"]),
                         self._format_dt(box["updated_at"]),
                         box["current_version"]])
                print(table)
            else:
                print("No boxes available for %s" % data["username"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("No such user '%s'" % args.username)
                return 1
            else:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                raise

    def _box_exists(self, tag):
        try:
            self._get("/box/" + tag)
            return True
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return False
            else:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                raise

    def box_info(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        try:
            r = self._get("/box/" + args.tag)
        except requests.HTTPError as e:
            data = e.response.json()
            for error in data["errors"]:
                print("Error: %s" % error)
            raise
        data = r.json()
        print("Details for '%s'" % data["tag"])
        if data["short_description"]:
            print("Description: %s\n" % data["short_description"])
        if len(data["versions"]) > 0:
            print("Available versions:")
            table = prettytable.PrettyTable(["Version", "Created", "Updated", "Providers"])
            for box in data["versions"]:
                if len(box["providers"]) > 0:
                    providers = []
                    for provider in box["providers"]:
                        providers.append(provider["name"])
                else:
                    providers = ["None"]
                table.add_row([box["version"], self._format_dt(box["created_at"]), self._format_dt(box["updated_at"]),
                               ", ".join(providers)])
            print(table)
        else:
            print("No versions available")

    def box_create(self, args):
        data = {
            "box": {
                "username": args.username,
                "name": args.box,
                "short_description": args.description,
                "is_private": args.private
            }
        }

        try:
            r = self._post("/boxes", data)
            data = r.json()
            print("Box '%s' created successfully" % data["tag"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                print("Error: Box '%s/%s' already exists" % (args.username, args.box))
                return 1
            else:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                raise

    def box_update(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        data = {"box": {}}
        values = 0

        if args.name:
            data["box"].update({"name": args.box})
            values += 1
        if args.description:
            data["box"].update({"short_description": args.description})
            values += 1
        if args.private:
            data["box"].update({"is_private": args.private})
            values += 1
        if args.public:
            data["box"].update({"is_private": ~ args.public})
            values += 1

        if values == 0:
            self.parser.error("no arguments given")
            exit(2)
        try:
            r = self._put("/box/" + args.tag, data)
            data = r.json()
            print("Box '%s' updated successfully" % data["tag"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Specified box does not exist")
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                raise

    def box_delete(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        if not args.force:
            answer = input("Do you really want to delete the box '%s'? [y/N] " % args.tag)
            if answer.lower() != "y" and answer.lower() != "yes":
                return

        try:
            r = self._delete("/box/" + args.tag)
            data = r.json()
            print("Box '%s' deleted successfully" % data["tag"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Box '%s' does not exist" % args.tag)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_version_info(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        try:
            r = self._get("/box/" + args.tag + "/version/" + args.version)
            data = r.json()
            print("Version information for '%s' v%s" % (args.tag, args.version))
            if len(data["providers"]) > 0:
                table = prettytable.PrettyTable(["Provider", "Created", "Updated"])
                for provider in data["providers"]:
                    table.add_row([provider["name"], self._format_dt(provider["created_at"]),
                                   self._format_dt(provider["updated_at"])])
                print(table)
            else:
                print("No providers available")
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Version '%s' of specified box does not exist" % args.version)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_version_create(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        data = {
            "version": {
                "version": args.version,
                "description": args.description
            }
        }

        try:
            r = self._post("/box/" + args.tag + "/versions", data)
            data = r.json()
            print("Version '%s' created successfully" % data["version"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_version_update(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        data = {
            "version": {}
        }

        values = 0

        if args.newversion:
            data["version"].update({"version": args.newversion})
            values += 1
        if args.description:
            data["version"].update({"description": args.description})
            values += 1

        if values == 0:
            self.parser.error("no arguments given")
            exit(2)

        try:
            self._put("/box/" + args.tag + "/version/" + args.version, data)
            print("Version '%s' updated successfully" % args.version)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("404")
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_version_delete(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        if not args.force:
            answer = input(
                "Do you really want to delete the version %s from box %s? [y/N] " % (args.version, args.tag))
            if answer.lower() != "y" and answer.lower() != "yes":
                return

        try:
            r = self._delete("/box/" + args.tag + "/version/" + args.version)
            data = r.json()
            print("Version '%s' deleted successfully" % data["version"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Version '%s' does not exist" % args.version)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_version_release(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        try:
            r = self._put("/box/" + args.tag + "/version/" + args.version + "/release")
            data = r.json()
            print("Version '%s' released successfully" % data["version"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Version '%s' does not exist" % args.version)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_version_revoke(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        try:
            r = self._put("/box/" + args.tag + "/version/" + args.version + "/revoke")
            data = r.json()
            print("Version '%s' revoked successfully" % data["version"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Version '%s' does not exist" % args.version)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_provider_info(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        try:
            r = self._get("/box/" + args.tag + "/version/" + args.version + "/provider/" + args.provider)
            data = r.json()
            print("Information for provider '%s' for '%s' v%s" % (data["name"], args.tag, args.version))
            print("Created: %s" % self._format_dt(data["created_at"]))
            print("Updated: %s" % self._format_dt(data["updated_at"]))
            print("Download URL: %s" % data["download_url"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Provider '%s' of specified box does not exist" % args.provider)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_provider_create(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        data = {
            "provider": {
                "name": args.provider,
                "url": args.url
            }
        }

        try:
            r = self._post("/box/" + args.tag + "/version/" + args.version + "/providers", data)
            data = r.json()
            print("Provider '%s' created successfully" % data["name"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_provider_update(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        data = {
            "version": {}
        }

        values = 0

        if args.newprovider:
            data["provider"].update({"name": args.newprovider})
            values += 1
        if args.url:
            data["provider"].update({"url": args.url})
            values += 1

        if values == 0:
            self.parser.error("no arguments given")
            exit(2)

        try:
            self._put("/box/" + args.tag + "/version/" + args.version + "/provider/" + args.provider, data)
            print("Provider '%s' updated successfully" % args.provider)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_provider_delete(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        if not args.force:
            answer = input(
                "Do you really want to delete the provider %s from version v%s of box %s? [y/N] " %
                (args.provider, args.version, args.tag))
            if answer.lower() != "y" and answer.lower() != "yes":
                return

        try:
            r = self._delete("/box/" + args.tag + "/version/" + args.version + "/provider/" + args.provider)
            data = r.json()
            print("Provider '%s' deleted successfully" % data["name"])
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Provider '%s' does not exist" % args.provider)
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

    def box_provider_upload(self, args):
        if not self._box_exists(args.tag):
            print("Box '%s' does not exist" % args.tag)
            return 1

        try:
            r = self._get("/box/" + args.tag + "/version/" + args.version + "/provider/" + args.provider + "/upload")
            data = r.json()
            upload_path = data["upload_path"]
            try:
                self._upload(upload_path, args.file)
                print("Provider '%s' uploaded successfully" % args.provider)
            except requests.HTTPError as e:
                raise
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                print("Error: Provider does not exist")
                return 1
            elif e.response.status_code == 403:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            elif e.response.status_code == 422:
                data = e.response.json()
                for error in data["errors"]:
                    print("Error: %s" % error)
                return 1
            else:
                raise

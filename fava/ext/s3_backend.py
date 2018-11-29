import click
import codecs
import boto3
from fava.core.file import FileModule


class S3Key():
    def __init__(self, bucket=None, obj=None, valid=True):
        self.bucket = bucket
        self.object = obj
        self.valid = valid


def get_s3_key(path):
    if path.startswith('s3://'):
        key_parts = path[5:].split('/')  # split path after s3://
        print(key_parts)
        return S3Key(key_parts[0], "/".join(key_parts[1:]))
    else:
        return S3Key(valid=False)


class FileOrS3URI(click.ParamType):
    def convert(self, value, param, ctx):
        if value.startswith('s3://'):
            return value
        else:
            path = click.Path(exists=True, dir_okay=False, resolve_path=True)
            return path.convert(value, param, ctx)


class S3FileBackend(FileModule):
    def __init__(self, fava_ledger, path):
        super().__init__(fava_ledger)  # ewww
        self.path = path
        self.s3_key = get_s3_key(path)

        # if this is an S3 file copy it to a local temp file
        self.s3resource = boto3.resource('s3')
        if self.s3_key.valid:
            self.s3resource.Bucket(self.s3_key.bucket).download_file(self.s3_key.object, '/tmp/hello.beancount')
            print('loaded')
        else:
            print('not a valid S3Key')

    @property
    def active(self):
        return self.s3_key.valid

    @property
    def beancount_file_path(self):
        return "/tmp/hello.beancount"

    def set_source(self, path, source, sha256sum):
        s3_obj = self.s3resource.Object(self.s3_key.bucket, self.s3_key.object)
        s3_obj.put(Body=codecs.encode(source))

        return super().set_source(path, source, sha256sum)

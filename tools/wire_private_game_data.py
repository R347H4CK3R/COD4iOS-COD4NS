from pathlib import Path
p=Path(__file__).resolve().parents[1]/'ports/ios/app/engine_app.mm'
s=p.read_text(encoding='utf-8')
anchor='- (void)startIfReady\n{'
addition='''- (BOOL)installBundledGameDataIfNeeded:(NSString *)root error:(NSError **)error
{
    if ([self hasGameData:root])
        return YES;
    NSString *bundleRoot = [NSBundle.mainBundle.resourcePath stringByAppendingPathComponent:@"PrivateGameData"];
    if (![self hasGameData:bundleRoot])
        return NO;
    NSFileManager *fm = NSFileManager.defaultManager;
    for (NSString *name in @[@"main", @"zone", @"localization.txt"])
    {
        NSString *destination = [root stringByAppendingPathComponent:name];
        if ([fm fileExistsAtPath:destination])
            continue; // Never replace existing user data.
        NSString *source = [bundleRoot stringByAppendingPathComponent:name];
        if (![fm copyItemAtPath:source toPath:destination error:error])
            return NO;
    }
    return [self hasGameData:root];
}

'''
if 'installBundledGameDataIfNeeded:' not in s:
 assert anchor in s
 s=s.replace(anchor,addition+anchor,1)
line='    NSString *root = [self documentsPath];\n    if (![self hasGameData:root])'
replace='''    NSString *root = [self documentsPath];
    NSError *bundleError = nil;
    if (![self hasGameData:root])
        [self installBundledGameDataIfNeeded:root error:&bundleError];
    if (bundleError)
    {
        _status.text = [NSString stringWithFormat:@"Bundled game data installation failed: %@", bundleError.localizedDescription];
        return;
    }
    if (![self hasGameData:root])'''
assert line in s or replace in s
if replace not in s:s=s.replace(line,replace,1)
p.write_text(s,encoding='utf-8')
print('Bundled data import installed')
